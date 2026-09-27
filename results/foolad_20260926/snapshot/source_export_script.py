from pathlib import Path
import pytse_client as tse

output = Path("exports")
output.mkdir(exist_ok=True)

for label, adjusted in (("unadjusted", False), ("adjusted", True)):
    data = tse.download(
        symbols="فولاد",
        adjust=adjusted,
        include_jdate=True,
        write_to_csv=False,
    )["فولاد"]

    if data.empty:
        raise RuntimeError(f"No {label} rows were returned")

    path = output / f"foolad_{label}_full_history.csv"
    data.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"{path}: {len(data)} rows")
    print("Columns:", list(data.columns))
    print("Date range:", data["date"].min(), "to", data["date"].max())