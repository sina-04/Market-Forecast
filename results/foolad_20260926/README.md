# Foolad — completed A100 experiment

Frozen five-year TSETMC history: 2021-09-26 through 2026-09-26. Run `0fae8c8d8bf0`.
The experiment forecasts the next observed traded session's adjusted official closing price in rials.
Corporate-action adjustment uses later information; this is retrospective research.

- [Executed notebook with outputs](marketforecast_executed.ipynb)
- [English report](run/report.md)
- [Metrics](run/test_metrics.json) and [134 aligned predictions](run/test_predictions.csv)
- [Selected Keras model](run/model.keras) and [HDF5 model](run/model.h5)
- [Independent fresh-kernel reload evidence](run/fresh_kernel_verification.json)
- [Raw snapshot and original exports](snapshot/), [cleaned data](run/cleaned.csv), [features](run/features.csv)
- `run/` also contains sequences, scalers, all candidate checkpoints/histories, audits, configuration,
  source commit/hashes, and environment metadata.

Validation selected 60 sessions and 64 LSTM units. Test RMSE: persistence **60.801**, Ridge 261.746,
OHLCV LSTM 390.777, engineered LSTM 467.071 adjusted rials. No model tuning followed test inspection.

## Print-quality charts

The figures were re-rendered from saved CSVs and training histories without retraining or changing predictions.
PNG files are 600 DPI; PDF and SVG retain scalable lines and text.

| Chart | PNG | PDF | SVG |
|---|---|---|---|
| Adjusted price history | [PNG](run/adjusted_close_history.png) | [PDF](run/adjusted_close_history.pdf) | [SVG](run/adjusted_close_history.svg) |
| Selected LSTM loss | [PNG](run/loss_selected_lstm.png) | [PDF](run/loss_selected_lstm.pdf) | [SVG](run/loss_selected_lstm.svg) |
| OHLCV LSTM loss | [PNG](run/loss_ohlcv_lstm.png) | [PDF](run/loss_ohlcv_lstm.pdf) | [SVG](run/loss_ohlcv_lstm.svg) |
| Forecast comparison | [PNG](run/test_forecasts.png) | [PDF](run/test_forecasts.pdf) | [SVG](run/test_forecasts.svg) |
| LSTM residuals | [PNG](run/residuals.png) | [PDF](run/residuals.pdf) | [SVG](run/residuals.svg) |

Recreate the figures from the repository root after installing the project:

```sh
python tools/export_charts.py --run results/foolad_20260926/run
```

Check saved models with the Colab dependencies installed:

```sh
marketforecast verify --run results/foolad_20260926/run
```

To rerun training on the frozen snapshot, copy `snapshot/` to `MyDrive/MarketForecast/data/snapshot/`
and run the guided notebook on `main`. The executed notebook preserves the original training commit
and code as execution evidence; its title and embedded charts were updated for this publication.
Original models, CSVs, scalers, histories, and metadata retain their original bytes. `checksums.json`
covers the published files, including the newly rendered figures. The historical training source hashes
remain unchanged and describe the training commit, rather than this later presentation update.
