"""Metrics in original adjusted rial units and reproducible figures."""
import numpy as np


def metrics(actual, predicted):
    actual, predicted = np.asarray(actual).reshape(-1), np.asarray(predicted).reshape(-1)
    if actual.shape != predicted.shape or not np.isfinite([actual, predicted]).all():
        raise ValueError("Predictions and actual values must be finite and aligned")
    error = predicted - actual
    mse = float(np.mean(error ** 2))
    nonzero = actual != 0
    return {"MAE": float(np.mean(np.abs(error))), "MSE": mse, "RMSE": float(np.sqrt(mse)),
            "MAPE": float(np.mean(np.abs(error[nonzero] / actual[nonzero])) * 100) if nonzero.any() else None,
            "samples": int(len(actual))}


def plots(output, predictions, histories):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path
    output = Path(output)
    for name, history in histories.items():
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(history["loss"], label="Training MSE (scaled)")
        ax.plot(history["val_loss"], label="Validation MSE (scaled)")
        ax.set(xlabel="Epoch", ylabel="MSE", title=name)
        ax.legend()
        fig.tight_layout()
        fig.savefig(output / f"loss_{name}.png", dpi=150)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(12, 5))
    for column in ["actual", "lstm", "persistence", "ridge", "ohlcv_lstm"]:
        ax.plot(predictions["date"], predictions[column], label=column, alpha=0.8)
    ax.set(xlabel="Test session", ylabel="Adjusted official closing price (rial)")
    ax.tick_params(axis="x", rotation=45)
    ax.xaxis.set_major_locator(plt.MaxNLocator(8))
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "test_forecasts.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    errors = predictions["lstm"] - predictions["actual"]
    axes[0].plot(errors.to_numpy())
    axes[0].axhline(0, color="black", linewidth=1)
    axes[0].set(xlabel="Test observation", ylabel="LSTM residual (rial)")
    axes[1].hist(errors, bins=30)
    axes[1].set(xlabel="Residual (rial)", ylabel="Count")
    fig.tight_layout()
    fig.savefig(output / "residuals.png", dpi=150)
    plt.close(fig)
