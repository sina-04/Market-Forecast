"""Small validation-only search, checkpointing, and sealed final evaluation."""
from pathlib import Path
import importlib.metadata
import platform
import random

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from .evaluation import metrics, plots
from .features import OHLCV_FEATURES
from .io import read_json, write_json
from .sequences import prepare


def build_model(tf, length, feature_count, units, config):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(length, feature_count)),
        tf.keras.layers.LSTM(units),
        tf.keras.layers.Dropout(config["dropout"]),
        tf.keras.layers.Dense(1),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=config["learning_rate"]), loss="mse")
    return model


def fit_candidate(tf, directory, splits, length, units, config):
    directory.mkdir(parents=True, exist_ok=True)
    checkpoint = directory / "best.keras"
    history_path = directory / "history.json"
    if checkpoint.exists() and history_path.exists():
        return tf.keras.models.load_model(checkpoint, compile=False), read_json(history_path)
    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(config["seed"])
    model = build_model(tf, length, splits["train"]["X"].shape[-1], units, config)
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=config["patience"], restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(str(checkpoint), monitor="val_loss", save_best_only=True),
        tf.keras.callbacks.CSVLogger(str(directory / "epochs.csv")),
        tf.keras.callbacks.TerminateOnNaN(),
    ]
    # Explicit bounded datasets avoid large default private thread pools on CPU runtimes.
    def dataset(split):
        data = tf.data.Dataset.from_tensor_slices((split["X"], split["y"])).batch(config["batch_size"])
        options = tf.data.Options()
        options.threading.private_threadpool_size = 1
        return data.with_options(options).prefetch(1)
    history = model.fit(dataset(splits["train"]), validation_data=dataset(splits["validation"]),
                        epochs=config["epochs"], callbacks=callbacks, verbose=2).history
    if not history["val_loss"] or not np.isfinite(history["val_loss"]).all():
        raise RuntimeError("Nonfinite training/validation losses; candidate is not usable")
    write_json(history_path, history)
    return tf.keras.models.load_model(checkpoint, compile=False), history


def predict_original(model, x, scaler):
    # Direct eager inference avoids rebuilding a tf.data pool for every small prediction.
    predictions = np.concatenate([model(x[i:i + 256], training=False).numpy() for i in range(0, len(x), 256)])
    return scaler.inverse_transform(predictions).ravel()


def train(output, frame, names, plan, config, manifest, audits):
    import tensorflow as tf
    output = Path(output)
    random.seed(config["seed"])
    np.random.seed(config["seed"])
    tf.keras.utils.set_random_seed(config["seed"])
    try:
        tf.config.experimental.enable_op_determinism()
    except (AttributeError, RuntimeError):
        pass
    write_json(output / "environment.json", {
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": {p: importlib.metadata.version(p) for p in ["tensorflow", "numpy", "pandas", "scikit-learn", "requests", "jdatetime", "h5py", "joblib"]},
        "devices": [d.name for d in tf.config.list_physical_devices()], "seed": config["seed"],
    })
    candidates = []
    for length in config["sequence_lengths"]:
        splits, xs, ys = prepare(frame, names, length, plan)
        for units in config["lstm_units"]:
            label = f"lstm_{length}_{units}"
            print(f"Training/validating {label}", flush=True)
            model, _ = fit_candidate(tf, output / "candidates" / label, splits, length, units, config)
            prediction = predict_original(model, splits["validation"]["X"], ys)
            result = {"name": label, "length": length, "units": units,
                      **metrics(splits["validation"]["actual"], prediction)}
            candidates.append(result)
            write_json(output / "validation_search.json", candidates)
    selected = min(candidates, key=lambda r: r["RMSE"])
    splits, xs, ys = prepare(frame, names, selected["length"], plan)
    model = tf.keras.models.load_model(output / "candidates" / selected["name"] / "best.keras", compile=False)
    model.save(output / "model.keras")
    model.save(output / "model.h5")
    joblib.dump({"features": xs, "target": ys}, output / "scalers.joblib")
    write_json(output / "model_metadata.json", {
        "selected": selected, "feature_order": names,
        "target": "next observed session adj_official_close", "unit": "retrospectively adjusted rial",
        "adjustment_basis_date": manifest["end_date"], "snapshot_checksums": manifest["checksums"],
        "cutoffs": {name: {"first_target": str(split["dates"][0]), "last_target": str(split["dates"][-1]), "samples": len(split["y"])}
                    for name, split in splits.items()},
    })
    for name, split in splits.items():
        np.savez_compressed(output / f"sequences_{name}.npz", **split)
    # Ridge alpha selection uses validation only and the same selected-length inputs.
    ridge_scores = []
    ridge_x = {key: split["X"].reshape(len(split["X"]), -1) for key, split in splits.items()}
    for alpha in config["ridge_alphas"]:
        estimator = Ridge(alpha=alpha).fit(ridge_x["train"], splits["train"]["y"].ravel())
        predicted = ys.inverse_transform(estimator.predict(ridge_x["validation"]).reshape(-1, 1)).ravel()
        ridge_scores.append({"alpha": alpha, **metrics(splits["validation"]["actual"], predicted)})
    alpha = min(ridge_scores, key=lambda r: r["RMSE"])["alpha"]
    ridge = Ridge(alpha=alpha).fit(ridge_x["train"], splits["train"]["y"].ravel())
    joblib.dump(ridge, output / "ridge.joblib")
    write_json(output / "ridge_validation.json", ridge_scores)
    # Ablation holds architecture and target dates constant; fit independent scalers.
    base_splits, base_xs, base_ys = prepare(frame, OHLCV_FEATURES, selected["length"], plan)
    base_model, base_history = fit_candidate(tf, output / "candidates" / "ohlcv", base_splits, selected["length"], selected["units"], config)
    base_model.save(output / "ohlcv_model.keras")
    joblib.dump({"features": base_xs, "target": base_ys}, output / "ohlcv_scalers.joblib")
    # Only now access held-out targets and predictions.
    test = splits["test"]
    test_predictions = predict_original(model, test["X"], ys)
    reloaded = tf.keras.models.load_model(output / "model.keras", compile=False)
    restored = joblib.load(output / "scalers.joblib")
    reproduced = predict_original(reloaded, test["X"], restored["target"])
    np.testing.assert_allclose(test_predictions, reproduced, rtol=1e-6, atol=1e-3)
    legacy = tf.keras.models.load_model(output / "model.h5", compile=False)
    np.testing.assert_allclose(test_predictions, predict_original(legacy, test["X"], ys), rtol=1e-6, atol=1e-3)
    predictions = pd.DataFrame({
        "date": test["dates"], "actual": test["actual"], "lstm": test_predictions,
        "persistence": test["persistence"],
        "ridge": ys.inverse_transform(ridge.predict(ridge_x["test"]).reshape(-1, 1)).ravel(),
        "ohlcv_lstm": predict_original(base_model, base_splits["test"]["X"], base_ys),
    })
    results = {name: metrics(predictions["actual"], predictions[name]) for name in ["lstm", "persistence", "ridge", "ohlcv_lstm"]}
    predictions.to_csv(output / "test_predictions.csv", index=False)
    write_json(output / "test_metrics.json", results)
    histories = {"selected_lstm": read_json(output / "candidates" / selected["name"] / "history.json"), "ohlcv_lstm": base_history}
    plots(output, predictions, histories)
    write_report(output, manifest, audits, config, selected, results)
    write_json(output / "completion.json", {"status": "complete", "saved_model_reload_verified": True,
                                            "test_targets": len(test["y"]), "selected": selected})
    return results


def write_report(output, manifest, audits, config, selected, results):
    comparison = "\n".join(f"| {name} | {value['MAE']:.3f} | {value['RMSE']:.3f} | {value['MAPE']:.3f} |" for name, value in results.items())
    improvement = 100 * (1 - results["lstm"]["RMSE"] / results["persistence"]["RMSE"]) if results["persistence"]["RMSE"] else None
    conclusion = (f"LSTM test RMSE improvement against persistence: {improvement:.2f}% (negative means worse)."
                  if improvement is not None else "Persistence has zero RMSE; relative improvement is undefined.")
    metadata = read_json(output / "model_metadata.json")
    report = f"""# MarketForecast research report

## Objective and data
Predict فولاد's next observed traded session's adjusted official closing price after the current session.
Source: TSETMC HTTPS API. Period: {manifest['start_date']} to {manifest['end_date']}.
Retrieved: {manifest['retrieved_at_utc']}. Instrument IDs: {', '.join(manifest['instrument_ids'])}.
Prices are rials; volume is shares. The raw source, normalized raw CSV, and SHA-256 checksums are frozen.
Official closing price is pClosing (FinPy Final); pDrCotVal (FinPy Close) is last trade.

## Cleaning and corporate actions
{audits['cleaning']['raw_rows']} raw rows; {audits['cleaning']['clean_rows']} valid rows;
{audits['cleaning']['quarantined_rows']} quarantined rows. Reasons: {audits['cleaning']['reason_counts']}.
No synthetic holiday/suspension candles or price interpolation. Large raw moves are flagged, not automatically removed.
Backward adjustment multiplies price fields by the reverse cumulative product of next-session
previous official close / current official close. Final factor = 1. Volume is unchanged.
This uses future corporate-action information: the study is retrospective on a frozen adjustment basis,
not a point-in-time backtest, forecast of unadjusted transaction prices, or evidence of achievable profit.

## Features and chronological preparation
{audits['features']['usable_rows']} usable feature rows after {audits['features']['warmup_or_nonfinite_rows']} warm-up/nonfinite exclusions.
Features include OHLCV, lags, returns, SMA/EMA 5/10/20, volatility/extrema, Wilder RSI-14 and ATR-14,
MACD 12/26/9, Bollinger 20, volume ratios, interaction and calendar variables.
All rolling calculations use current/past observations only, on the fixed adjusted series.
Common eligible target dates are shared by all window lengths. Split fractions are
{config['train_fraction']:.0%} / {config['validation_fraction']:.0%} / {1-config['train_fraction']-config['validation_fraction']:.0%}.
Cutoffs: {metadata['cutoffs']}.
Input and target StandardScalers are fitted independently on training inputs/targets only.

## Models and selection
One LSTM layer; dropout {config['dropout']}; dense linear output; Adam {config['learning_rate']}; MSE loss;
batch size {config['batch_size']}; at most {config['epochs']} epochs; early stopping patience {config['patience']}.
Validation-only search: lengths {config['sequence_lengths']}, units {config['lstm_units']}.
Selected: length {selected['length']}, units {selected['units']}, validation RMSE {selected['RMSE']:.3f} adjusted rials.
Seed: {config['seed']}. Ridge alpha is selected on validation. OHLCV ablation uses the selected architecture.
The test set is evaluated only after all selections; no train-plus-validation refit.

## Held-out results
MAE and RMSE are adjusted rials; MAPE is percent. MSE is also recorded in test_metrics.json.

| Model | MAE | RMSE | MAPE (%) |
|---|---:|---:|---:|
{comparison}

{conclusion}
The result is descriptive; performance is not guaranteed on later market regimes.
Five years of one stock provide limited independent samples, and overlapping windows are correlated.
The study does not include transaction costs, tradability/queues, or a trading strategy.

## Reproducibility and artifacts
The environment, configuration, snapshot checksums, feature order, split dates, scalers,
candidate logs, selected .keras/.h5 models, sequences, predictions, metrics, and figures are saved together.
Both selected saved model formats were reloaded and verified against exported predictions.
See loss_selected_lstm.png, loss_ohlcv_lstm.png, test_forecasts.png, and residuals.png.
"""
    (Path(output) / "report.md").write_text(report, encoding="utf-8")

