# Foolad hourly forecast — completed A100 experiment

Training completed in Colab on an **NVIDIA A100-SXM4 with 40 GB GPU memory**.
The downloaded ZIP matches Colab's SHA-256, all 77 original files passed their checksums,
and the organized files retain their original bytes. Directory names are descriptive;
the original run identifier remains in provenance and model metadata.

## Results and models

- [Research report](training-results/hourly-forecast/report.md)
- [Full metrics](training-results/hourly-forecast/test_metrics.json) and [535 test predictions](training-results/hourly-forecast/test_predictions.csv)
- [Selected full-feature Keras model](training-results/hourly-forecast/model.keras) and [HDF5 model](training-results/hourly-forecast/model.h5)
- [OHLCV baseline model](training-results/hourly-forecast/ohlcv_model.keras)
- [Colab reload verification](training-results/hourly-forecast/fresh_kernel_verification.json)
- [Independent local verification](training-results/hourly-forecast/local_verification.json)
- [Frozen hourly data and coverage](data/snapshot/) and [source provenance](provenance/)

| Model | MAE (adjusted rials) | RMSE (adjusted rials) | MAPE (%) |
|---|---:|---:|---:|
| Full-feature LSTM | 22.646 | 33.049 | 0.935 |
| Persistence | **20.322** | 32.793 | **0.832** |
| Ridge | 52.373 | 99.132 | 2.149 |
| OHLCV-only LSTM | 22.452 | **32.143** | 0.923 |

Validation selected the full-feature LSTM with **60 observed bars and 32 units**.
Its test RMSE is 0.78% higher than persistence. The OHLCV comparison has 1.98% lower RMSE
than persistence, but higher MAE/MAPE. This secondary test result does not replace the
validation-selected model. No additional tuning or selection followed test inspection.

The target is the next observed hourly bar's adjusted last traded price, rather than the previous
daily experiment's official closing price. Their raw errors measure different horizons and targets.
There is no claim that additional hourly samples alone establish better accuracy.

## Folder guide

```text
foolad-hourly-a100/
  data/snapshot/                    frozen source files and coverage
  training-results/hourly-forecast/ models, scalers, predictions, reports and charts
    model-candidates/
      lstm-12-bars-32-units/
      lstm-12-bars-64-units/
      lstm-24-bars-32-units/
      lstm-24-bars-64-units/
      lstm-60-bars-32-units/         validation-selected full-feature candidate
      lstm-60-bars-64-units/
      ohlcv-baseline-lstm/
  provenance/                      original checksums and exact training source
```

The full dataset has 4,273 bars covering 1,025 trading dates, October 2, 2021 through
September 30, 2026. Fifteen unresolved dates remain explicit in coverage. Indicators restart
after those dates; windows crossing them are excluded. Splits contain 2,490 / 533 / 535 targets.
All source-returned hours are retained, including 236 bars at or after 13:00 with unverified
source session classification. Adjustments use the complete daily official-close chain and
are retrospective, applied uniformly to bars within each day.

## Verification and chart tools

Independent local checks reproduce all three sequence splits and all four exported metric sets.
The selected Keras/HDF5 models and Ridge reproduce the saved predictions within the original tolerance.
The OHLCV model agrees within 0.01 adjusted rial on CPU TensorFlow 2.19.1 versus the A100 training
environment's TensorFlow 2.20.0; the measured maximum difference is recorded in `local_verification.json`.
The original A100 predictions and metrics remain unchanged. The local suite passed 30 tests,
with one optional training integration test skipped.

From the project root, using the working Python 3.12 research environment:

```powershell
./.venv-research/Scripts/python.exe results/foolad-hourly-a100/provenance/verify_local_results.py
./.venv-research/Scripts/python.exe -m marketforecast.cli verify --run results/foolad-hourly-a100/training-results/hourly-forecast
./.venv-research/Scripts/python.exe tools/export_charts.py --run results/foolad-hourly-a100/training-results/hourly-forecast --output artifacts/hourly-charts
```

The chart exporter reads `candidate_directories.json` to find the renamed candidates.
Original training identifiers in metadata are preserved. `folder_layout.json` records the mapping,
`provenance/original_colab_bundle_checksums.json` retains the pre-rename manifest, and
`bundle_checksums.json` covers the organized package with its current paths.
The portable archive is [`artifacts/foolad-hourly-a100-results.zip`](../../artifacts/foolad-hourly-a100-results.zip).

The original execution is available in the [Colab notebook](https://colab.research.google.com/drive/1D-44hmBqUJeaw57meHDSLm1P1fc6xUdy).
The portable setup notebook is `notebooks/marketforecast_hourly_colab.ipynb` in the project root.
