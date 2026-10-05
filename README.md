# Market-Forecast

Reproducible internship research for **فولاد**. The current hourly experiment forecasts the next observed
traded bar's **adjusted last traded price**; the preserved daily experiment forecasts official closing price.

## Hourly experiment

The [completed hourly A100 results](results/foolad-hourly-a100/README.md) contain the verified downloaded
snapshot, trained models, predictions, candidate histories, reports and charts in descriptive folders.
On 535 test targets, the validation-selected full-feature LSTM has RMSE 33.049 adjusted rials versus
persistence 32.793. The OHLCV comparison has RMSE 32.143; persistence retains the lowest MAE/MAPE.

The October 5, 2026 export contains 4,273 bars from October 2, 2021 through September 30, 2026,
covering 1,025 trading dates; 15 source dates are unresolved. The importer verifies every exported bar
against the cached returned trades and freezes the hourly CSV, daily adjustment basis, coverage and hashes.
Daily corporate-action factors apply uniformly within each session. Indicators restart after known missing
dates, and sequences crossing those dates are excluded. Overnight/weekend gaps remain observed-bar gaps.

```powershell
./.venv-research/Scripts/python.exe -m marketforecast.cli import-hourly --config configs/hourly.json --root artifacts/foolad_hourly_20261005 --hourly exports/foolad_hourly/foolad_hourly.csv --daily exports/foolad_hourly/daily_unadjusted.csv --coverage exports/foolad_hourly/coverage.csv --export-script export_foolad_hourly.py --trades exports/foolad_hourly/returned_trades
./.venv-research/Scripts/python.exe -m marketforecast.cli prepare --config configs/hourly.json --root artifacts/foolad_hourly_20261005
./.venv-research/Scripts/python.exe tools/build_hourly_colab.py
```

Open `notebooks/marketforecast_hourly_colab.ipynb` in Colab, select A100 GPU, run the training cell and
upload `artifacts/foolad_hourly_20261005/colab/foolad_hourly_training_input.zip`. The ZIP uses the exact
local source files, including current changes, instead of fetching an older daily pipeline from GitHub.
The notebook verifies checksums, runs tests, trains, verifies saved models and downloads the results ZIP.
Download outputs before disconnecting; this notebook uses temporary runtime storage.

Hourly inputs use relative prices, normalized indicators, log/relative volume and hour/calendar features.
The LSTM learns next-bar log return and reconstructs adjusted price using the prior observed bar.
Validation selects among 12/24/60-bar contexts × 32/64 units. Persistence, Ridge and OHLCV use common
chronological target timestamps with training-only scalers. `configs/hourly.json` enforces an A100.
More hourly bars do not guarantee lower errors, and hourly-last-price versus daily-official-close errors
measure different targets/horizons. Conclusions use the held-out hourly baseline comparison.

[Open in Colab](https://colab.research.google.com/github/sina-04/Market-Forecast/blob/main/notebooks/marketforecast_colab.ipynb)

## Completed Foolad experiment

The [published results](results/foolad_20260926/README.md) include the frozen snapshot, cleaned data,
features, sequences, scalers, trained models, executed notebook, predictions, and English report.
Training used an A100 with 80 GB GPU memory. Persistence won the held-out comparison; the selected
LSTM did not outperform it. All five charts are available as 600-DPI PNG and vector PDF/SVG files.

## Priorities

1. Frozen source responses and raw CSV with provenance and SHA-256 checksums.
2. Cleaned CSV and explicit quarantine audit.
3. Feature CSV with causal indicators, statistics, volume, and calendar inputs.
4. Chronological 70/15/15 sequences and training-only scalers.
5. Colab training, loss plots, and selected `.keras` / `.h5` models.
6. Held-out MAE/MSE/RMSE/MAPE and persistence/Ridge/OHLCV comparisons.
7. Generated English research report and results archive.

Actual deliverables require verified real-data acquisition and training. Test fixtures never substitute for real
TSETMC data or establish market performance. See [execution status](docs/implementation_status.md).

## Colab

Run notebook cells in order. Select an available A100 GPU for the recorded experiment;
the small model also supports other GPUs or CPU. Default persistence is `MyDrive/MarketForecast`.
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

For unchanged user-supplied adjusted and unadjusted exports:

```powershell
python -m marketforecast.cli import --root artifacts/foolad_20260926 --unadjusted exports/foolad_unadjusted_full_history.csv --adjusted exports/foolad_adjusted_full_history.csv --export-script export_foolad.py
python -m marketforecast.cli prepare --root artifacts/foolad_20260926
```

The importer preserves both originals, validates date/activity agreement and Jalali conversion,
and independently recalculates adjusted prices within the export's half-rial rounding tolerance.
Original retrieval time, package version, and HTTP bodies remain explicitly unavailable when not
recorded by the source exporter. Copy the complete frozen snapshot to Drive before training.

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
For verified export imports, a candle with only a zero opening price may be quarantined while its
valid official-close reference remains in the complete adjustment basis. No price is invented.
Source session numbering excludes every target/window crossing the quarantined session.
Official close may lie outside traded high/low due to market rules; candle checks apply to open/last trade.

Backward adjustment accumulates next-session previous official close / current official close.
This uses later corporate-action information: results are **retrospective adjusted-price research**,
not a point-in-time trading backtest or an unadjusted transaction-price forecast.
Features are causal conditional on a fixed adjustment basis.

All candidates share target dates. Scalers see training inputs/targets only. The LSTM has one recurrent
layer, dropout and a linear head. Ridge and OHLCV comparisons use the same dates; test data never selects
architecture, sequence length, Ridge alpha, or epoch. See [full data contract](docs/methodology.md).

## Outputs

`ROOT/data/snapshot/`: original API responses or original user CSV exports, `raw.csv`, checksummed manifest;
export imports also retain an independently verified complete adjustment basis.

`ROOT/runs/<fingerprint>/`: cleaned/features CSVs, quarantine/audits, default and selected sequences,
scalers, checkpoints, configuration/environment, feature order, metadata, models, predictions,
metrics, loss/forecast/residual figures, and `report.md`.

`ROOT/artifacts/marketforecast_<fingerprint>.zip`: portable data/results archive with checksums.
`completion.json` appears only after evaluation and model reload verification succeed.

Working datasets/models and notebook outputs are excluded from Git. The verified, frozen
`results/foolad_20260926/` publication is explicitly included; credentials are never committed.
Docker, more stocks, trading UI, and extensive searches are deferred.
See the [original instructions](Financial_Market_LSTM_Project_Instructions_EN.md).

