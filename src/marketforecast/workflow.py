"""Stages shared by local CLI and Colab notebook."""
from pathlib import Path
import hashlib
import json
import shutil

import pandas as pd

from .data import adjust_prices, clean, collect, validate_snapshot
from .features import engineer
from .io import checksum, read_json, write_json
from .sequences import make_plan, prepare


def prepare_run(root, config):
    snapshot = Path(root) / "data" / "snapshot"
    manifest = validate_snapshot(snapshot)
    if (manifest["symbol"] != config["symbol"] or manifest["years"] != config["years"]
            or manifest["company_contains"] != config["company_contains"]):
        raise ValueError("Config disagrees with frozen snapshot; use another root for a new experiment")
    source_hashes = {p.name: hashlib.sha256(p.read_text(encoding="utf-8").encode()).hexdigest()
                     for p in Path(__file__).parent.glob("*.py")}
    fingerprint = hashlib.sha256(json.dumps({"snapshot": manifest["checksums"], "config": config,
                                            "source_hashes": source_hashes}, sort_keys=True).encode()).hexdigest()[:12]
    output = Path(root) / "runs" / fingerprint
    output.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(snapshot / "raw.csv", dtype={"instrument_id": str})
    cleaned, rejected, audit = clean(raw)
    rejected.to_csv(output / "quarantine.csv", index=False)
    write_json(output / "cleaning_audit.json", audit)
    # A discarded actual-trade record breaks the adjustment chain. Require repair rather than hiding it.
    harmless = rejected["reason"].isin(["identical_duplicate", "no_actual_trades"])
    if not audit["adjustment_safe"] or (~harmless).any():
        cleaned.to_csv(output / "cleaned_unadjusted.csv", index=False)
        raise ValueError(f"Data audit requires review before adjustment: {output / 'quarantine.csv'}")
    cleaned = adjust_prices(cleaned)
    cleaned["session_number"] = range(len(cleaned))
    cleaned.to_csv(output / "cleaned.csv", index=False)
    frame, names, feature_audit = engineer(cleaned)
    frame.to_csv(output / "features.csv", index=False)
    write_json(output / "feature_audit.json", feature_audit)
    write_json(output / "config.json", config)
    write_json(output / "snapshot_manifest.json", manifest)
    write_json(output / "feature_order.json", names)
    write_json(output / "source_hashes.json", source_hashes)
    if (Path(root) / "source_commit.json").exists():
        shutil.copy2(Path(root) / "source_commit.json", output / "source_commit.json")
    plan = make_plan(frame, config)
    import joblib
    import numpy as np
    initial_splits, xs, ys = prepare(frame, names, config["default_sequence_length"], plan)
    for name, split in initial_splits.items():
        np.savez_compressed(output / f"initial_sequences_{name}.npz", **split)
    joblib.dump({"features": xs, "target": ys}, output / "initial_scalers.joblib")
    return output, frame, names, plan, manifest, {"cleaning": audit, "features": feature_audit}


def run(root, config, acquire=True):
    if acquire:
        collect(root, config)
    output, frame, names, plan, manifest, audits = prepare_run(root, config)
    if (output / "completion.json").exists():
        verify_run(output)
        return output
    from .training import train
    train(output, frame, names, plan, config, manifest, audits)
    write_json(Path(root) / "latest_run.json", {"run": str(output.resolve())})
    export_bundle(root, output)
    return output


def verify_run(output):
    import joblib
    import numpy as np
    import tensorflow as tf
    from .training import predict_original
    output = Path(output)
    metadata = read_json(output / "model_metadata.json")
    scalers = joblib.load(output / "scalers.joblib")
    features = pd.read_csv(output / "features.csv")
    values = features[metadata["feature_order"]].to_numpy(float)
    test = np.load(output / "sequences_test.npz", allow_pickle=False)
    scaled = scalers["features"].transform(values)
    length = metadata["selected"]["length"]
    x = np.stack([scaled[t-length:t] for t in test["target_positions"]]).astype("float32")
    np.testing.assert_allclose(x, test["X"], atol=1e-5)
    exported = pd.read_csv(output / "test_predictions.csv")
    np.testing.assert_array_equal(test["dates"], exported["date"].to_numpy())
    np.testing.assert_allclose(test["actual"], exported["actual"], rtol=1e-10)
    for filename in ["model.keras", "model.h5"]:
        model = tf.keras.models.load_model(output / filename, compile=False)
        predicted = predict_original(model, x, scalers["target"])
        np.testing.assert_allclose(predicted, exported["lstm"], rtol=1e-6, atol=1e-3)
    return {"verified": True, "predictions": len(exported)}


def export_bundle(root, output):
    output = Path(output)
    root = Path(root)
    # Create a portable archive with the frozen data and selected research run.
    staging = root / "artifacts" / f"bundle_{output.name}"
    if staging.exists():
        # Refresh individual trees; no shell deletion and only named staging destinations.
        shutil.copytree(root / "data" / "snapshot", staging / "data" / "snapshot", dirs_exist_ok=True)
        shutil.copytree(output, staging / "runs" / output.name, dirs_exist_ok=True)
    else:
        staging.mkdir(parents=True)
        shutil.copytree(root / "data" / "snapshot", staging / "data" / "snapshot")
        shutil.copytree(output, staging / "runs" / output.name)
    write_json(staging / "bundle_checksums.json", {
        str(p.relative_to(staging)): checksum(p) for p in staging.rglob("*") if p.is_file() and p.name != "bundle_checksums.json"
    })
    return Path(shutil.make_archive(str(root / "artifacts" / f"marketforecast_{output.name}"), "zip", staging))

