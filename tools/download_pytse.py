"""Try pytse-client's legacy export route with bounded retries and source capture.

Run in a separate environment: pytse-client requires jdatetime<4, whereas training uses jdatetime5.
This tool does not modify the frozen research snapshot. Its CSV needs validation/import before training.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="فولاد")
    parser.add_argument("--output", type=Path, default=Path("artifacts/pytse-download"))
    parser.add_argument("--https", action="store_true", help="Use HTTPS for the package's existing legacy export URL")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    import requests
    from tenacity import stop_after_attempt, wait_fixed
    import pytse_client as tse
    from pytse_client import symbols_data, tse_settings
    module = importlib.import_module("pytse_client.download")
    identity = symbols_data.symbols_information().get(args.symbol)
    if not identity:
        raise ValueError(f"No exact bundled symbol match: {args.symbol}")
    metadata = {
        "symbol": args.symbol, "identity": identity,
        "pytse_client_version": importlib.metadata.version("pytse-client"),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "adjust": False, "http_attempts_per_instrument": 2, "request_timeout_seconds": 10,
        "source": "https://github.com/Glyphack/pytse-client", "responses": [],
    }
    if args.https:
        tse_settings.TSE_TICKER_EXPORT_DATA_ADDRESS = tse_settings.TSE_TICKER_EXPORT_DATA_ADDRESS.replace("http://", "https://", 1)
    metadata["export_url_template"] = tse_settings.TSE_TICKER_EXPORT_DATA_ADDRESS

    class CapturingSession(requests.Session):
        def get(self, url, **kwargs):
            response = super().get(url, **kwargs)
            filename = f"response_{len(metadata['responses']):02d}.txt"
            (args.output / filename).write_bytes(response.content)
            metadata["responses"].append({"url": response.url, "status": response.status_code,
                                          "file": filename, "sha256": hashlib.sha256(response.content).hexdigest()})
            return response

    # The upstream HTTPError retry has no stop condition; bound it for this attempt.
    module.requests_retry_session = CapturingSession
    module.download_ticker_daily_record = module.download_ticker_daily_record.retry_with(
        stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
    print(json.dumps({"identity": identity, "url": metadata["export_url_template"]}, ensure_ascii=False), flush=True)
    try:
        result = tse.download(symbols=args.symbol, write_to_csv=False, include_jdate=True, adjust=False)
        frame = result.get(args.symbol)
        required = {"date", "open", "high", "low", "adjClose", "close", "volume", "count", "value", "yesterday"}
        if frame is None or frame.empty or not required.issubset(frame.columns):
            raise ValueError("No usable history with all required fields")
        destination = args.output / "foolad_unadjusted.csv"
        frame.to_csv(destination, index=False, encoding="utf-8-sig")
        metadata.update(status="downloaded_needs_validation", rows=len(frame),
                        first_date=str(frame.date.min()), last_date=str(frame.date.max()),
                        csv=destination.name, csv_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                        field_mapping={"adjClose": "official_close (unadjusted because adjust=False)",
                                       "close": "last_trade", "yesterday": "previous_official_close"})
        print(f"Downloaded {len(frame)} rows to {destination}", flush=True)
    except Exception as error:
        metadata.update(status="failed", error=f"{type(error).__name__}: {error}")
        print(metadata["error"], file=sys.stderr, flush=True)
    finally:
        (args.output / "download_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if metadata["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
