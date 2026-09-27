# MarketForecast

Reproducible internship research for **فولاد**, forecasting the next observed traded session's
**adjusted official closing price (قیمت پایانی)** from five years of daily TSETMC data.

[Open in Colab](https://colab.research.google.com/github/sina-04/MarketForecast/blob/codex/tsetmc-colab/notebooks/marketforecast_colab.ipynb)

## Priorities

1. Frozen source responses and raw CSV with provenance and SHA-256 checksums.
2. Cleaned CSV and explicit quarantine audit.
3. Feature CSV with causal indicators, statistics, volume, and calendar inputs.
4. Chronological 70/15/15 sequences and training-only scalers.
5. Colab training, loss plots, and selected `.keras` / `.h5` models.
6. Held-out MAE/MSE/RMSE/MAPE and persistence/Ridge/OHLCV comparisons.
7. Generated English research report and results archive.

Actual deliverables require live-data collection and training. Test fixtures never substitute for real
TSETMC data or establish market performance. See [execution status](docs/implementation_status.md).

## Colab

Run notebook cells in order. GPU is optional. Default persistence is `MyDrive/MarketForecast`.
Six small LSTMs are selected on validation, then evaluated on held-out targets.
Best checkpoints persist after each validation improvement; completed candidates can be reused.
The source Git commit and environment are recorded. Use a new output root for a refreshed snapshot.

If Colab cannot reach TSETMC, collect locally and copy the **entire** `data/snapshot` directory to
the same path under the Drive output root. Cached data must pass integrity checks.
The first capture freezes five years ending before today's Tehran date.

### Alternative acquisition with pytse-client

The legacy TSETMC CSV export can also be attempted using [pytse-client](https://github.com/Glyphack/pytse-client).
Keep its older dependencies in a separate environment:

```powershell
py -3.12 -m venv .venv-pytse
./.venv-pytse/Scripts/python.exe -m pip install -r requirements-pytse.txt
./.venv-pytse/Scripts/python.exe tools/download_pytse.py
# Optional HTTPS attempt against the same legacy export route:
./.venv-pytse/Scripts/python.exe tools/download_pytse.py --https --output artifacts/pytse-download-https
```

The helper limits retries, captures original responses and download metadata, and exports unadjusted history.
In this package, unadjusted `adjClose` is official closing price, `close` is last trade, and `yesterday` is
previous official close. A successful CSV still needs validation/import before it becomes a frozen research
snapshot. It is not automatically treated as a completed project dataset.

## Local setup

Use Python 3.11–3.13 for training. Python 3.14 is unsupported. Local commands below use Python 3.12;
Colab's Python 3.13 selects TensorFlow 2.20 through the requirements file.

```powershell
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-colab.txt
./.venv/Scripts/python.exe -m pip install --no-deps -e .
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m marketforecast.cli collect --root artifacts/local
./.venv/Scripts/python.exe -m marketforecast.cli prepare --root artifacts/local
```

Training belongs in Colab; the same code supports a local CPU integration check:

```powershell
./.venv/Scripts/python.exe -m marketforecast.cli train --root artifacts/local
./.venv/Scripts/python.exe -m marketforecast.cli verify --run artifacts/local/runs/<run-id>
```

`all` combines collection/preparation/training. Completed runs are verified and reused;
frozen data is not silently refreshed. Interrupted candidates restart; completed candidates are reused.

## Methodology

TSETMC `pClosing` is official close; `pDrCotVal` is last trade. In
[FinPy-TSE](https://github.com/ARahimiQuant/finpy-tse), these are `Final` and `Close`.
Prices are rials, volumes shares, Gregorian dates drive computation, and Jalali dates are retained.
Holidays/suspensions remain gaps. Invalid records are quarantined; large moves are only flagged.
Other than identical duplicates and zero-trade sessions, exclusions stop preparation for review because
discarding traded observations can break the corporate-action adjustment chain.
Official close may lie outside traded high/low due to market rules; candle checks apply to open/last trade.

Backward adjustment accumulates next-session previous official close / current official close.
This uses later corporate-action information: results are **retrospective adjusted-price research**,
not a point-in-time trading backtest or an unadjusted transaction-price forecast.
Features are causal conditional on a fixed adjustment basis.

All candidates share target dates. Scalers see training inputs/targets only. The LSTM has one recurrent
layer, dropout and a linear head. Ridge and OHLCV comparisons use the same dates; test data never selects
architecture, sequence length, Ridge alpha, or epoch. See [full data contract](docs/methodology.md).

## Outputs

`ROOT/data/snapshot/`: search/history JSON, `raw.csv`, checksummed manifest.

`ROOT/runs/<fingerprint>/`: cleaned/features CSVs, quarantine/audits, default and selected sequences,
scalers, checkpoints, configuration/environment, feature order, metadata, models, predictions,
metrics, loss/forecast/residual figures, and `report.md`.

`ROOT/artifacts/marketforecast_<fingerprint>.zip`: portable data/results archive with checksums.
`completion.json` appears only after evaluation and model reload verification succeed.

Large datasets/models, credentials and notebook outputs are excluded from Git.
Docker, more stocks, trading UI, and extensive searches are deferred.
See the [original instructions](Financial_Market_LSTM_Project_Instructions_EN.md).

