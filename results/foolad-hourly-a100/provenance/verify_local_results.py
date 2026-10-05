"""Independently verify the organized Colab results; run from the project environment."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import platform
import sys
sys.dont_write_bytecode = True

import joblib
import numpy as np
import pandas as pd
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "provenance" / "training-source"))
from marketforecast.data import validate_snapshot
from marketforecast.evaluation import metrics
from marketforecast.features import ohlcv_features
from marketforecast.io import checksum, read_json, write_json
from marketforecast.sequences import make_plan, prepare
from marketforecast.training import predict_original, restore_prices
from marketforecast.workflow import verify_run


def main():
    layout = read_json(ROOT / "folder_layout.json")
    run = ROOT / layout["run_directory"]
    originals = read_json(ROOT / "provenance" / "original_colab_bundle_checksums.json")
    original_prefix = f"runs/{layout['original_run_id']}/"
    for original, expected in originals.items():
        relative = original.replace("\\", "/")
        if relative.startswith(original_prefix):
            suffix = relative[len(original_prefix):]
            for label, directory in layout["candidate_directories"].items():
                suffix = suffix.replace(f"candidates/{label}/", f"{directory}/")
            relative = f"{layout['run_directory']}/{suffix}"
        assert checksum(ROOT / relative) == expected, relative

    for filename, expected in read_json(run / "source_hashes.json").items():
        source = ROOT / "provenance" / "training-source" / "marketforecast" / filename
        actual = hashlib.sha256(source.read_text(encoding="utf-8").encode()).hexdigest()
        assert actual == expected, filename
    validate_snapshot(ROOT / "data" / "snapshot")
    metadata = read_json(run / "model_metadata.json")
    config = read_json(run / "config.json")
    frame = pd.read_csv(run / "features.csv")
    plan = make_plan(frame, config)
    splits, _, _ = prepare(frame, metadata["feature_order"], metadata["selected"]["length"], plan)
    for split_name, reproduced in splits.items():
        with np.load(run / f"sequences_{split_name}.npz", allow_pickle=False) as saved:
            for key, values in reproduced.items():
                if values.dtype.kind in "US":
                    np.testing.assert_array_equal(values, saved[key])
                else:
                    np.testing.assert_allclose(values, saved[key], rtol=1e-10, atol=1e-6)

    predictions = pd.read_csv(run / "test_predictions.csv")
    expected_metrics = read_json(run / "test_metrics.json")
    for model_name, expected in expected_metrics.items():
        observed = metrics(predictions["actual"], predictions[model_name])
        for metric_name, value in expected.items():
            np.testing.assert_allclose(observed[metric_name], value, rtol=1e-10)
    np.testing.assert_array_equal(splits["test"]["dates"], predictions["date"])
    np.testing.assert_allclose(splits["test"]["actual"], predictions["actual"], rtol=1e-10)
    assert predictions["date"].is_unique

    # This process reloads both selected model formats on the local CPU.
    selected_reload = verify_run(run)
    test = splits["test"]
    scalers = joblib.load(run / "scalers.joblib")
    ridge = joblib.load(run / "ridge.joblib")
    ridge_prediction = restore_prices(
        ridge.predict(test["X"].reshape(len(test["X"]), -1)),
        scalers["target"], test["persistence"], metadata["target_mode"],
    )
    np.testing.assert_allclose(ridge_prediction, predictions["ridge"], rtol=1e-6, atol=1e-3)
    base_splits, base_x, base_y = prepare(frame, ohlcv_features(frame), metadata["selected"]["length"], plan)
    base_scalers = joblib.load(run / "ohlcv_scalers.joblib")
    for name, reproduced in [("features", base_x), ("target", base_y)]:
        for attribute in ["mean_", "scale_"]:
            np.testing.assert_allclose(getattr(reproduced, attribute), getattr(base_scalers[name], attribute), rtol=1e-10)
    base_model = tf.keras.models.load_model(run / "ohlcv_model.keras", compile=False)
    base_prediction = predict_original(base_model, base_splits["test"]["X"], base_scalers["target"], test["persistence"], metadata["target_mode"])
    # CPU TensorFlow 2.19 versus A100 TensorFlow 2.20 uses different LSTM kernels.
    # Require absolute agreement within one hundredth of an adjusted rial.
    np.testing.assert_allclose(base_prediction, predictions["ohlcv_lstm"], rtol=0, atol=0.01)

    verification = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "original_archive_sha256": layout["original_archive_sha256"],
        "original_files_verified": len(originals),
        "training_source_hashes_verified": True,
        "snapshot_integrity_verified": True,
        "sequence_splits_reproduced": {name: len(split["dates"]) for name, split in splits.items()},
        "all_four_exported_metrics_reproduced": True,
        "selected_model_reload": selected_reload,
        "model_formats_reloaded": ["model.keras", "model.h5", "ohlcv_model.keras", "ridge.joblib"],
        "prediction_tolerance": {"rtol": 1e-6, "atol_adjusted_rials": 1e-3},
        "ohlcv_cpu_tolerance_adjusted_rials": 0.01,
        "ohlcv_max_absolute_prediction_difference": float(np.max(np.abs(base_prediction - predictions["ohlcv_lstm"]))),
        "ridge_max_absolute_prediction_difference": float(np.max(np.abs(ridge_prediction - predictions["ridge"]))),
        "local_environment": {"python": platform.python_version(), "tensorflow": tf.__version__, "keras": tf.keras.__version__, "devices": [d.name for d in tf.config.list_physical_devices()]},
        "training_environment": "Original Colab A100 environment retained in training-results/hourly-forecast/environment.json",
        "no_retraining_or_model_selection_performed": True,
    }
    write_json(run / "local_verification.json", verification)
    print(verification)


if __name__ == "__main__":
    main()
