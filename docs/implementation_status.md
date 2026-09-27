# Implementation and execution status

Acquisition, preparation, Colab training, model selection, evaluation, artifact verification, and reporting
are implemented. Live execution evidence is recorded here after verification.
Synthetic fixtures check behavior only; real-data deliverables require a successful `completion.json`.

## Data access checks — 2026-09-27

- Direct HTTPS TSETMC CDN search: connection timed out locally and in Colab.
- Installed and inspected `pytse-client` 0.19.1 and upstream source.
- Bundled فولاد identity: company فولاد مبارکه اصفهان, index `46348559193224090`, ISIN `IRO1FOLD0001`.
- Its legacy export at `old.tsetmc.com/tsev2/data/Export-txt.aspx` timed out over both HTTP and HTTPS,
  locally and in Colab. Direct acquisition did not produce a research snapshot.
- `tools/download_pytse.py` preserves original successful HTTP responses, metadata, and CSVs, with bounded
  retries. Use `requirements-pytse.txt` in an isolated acquisition environment because its older
  `jdatetime` dependency conflicts with the pinned training environment.
- In unadjusted pytse-client output, `adjClose` means official closing price and `close` means last trade.
  A download must be validated/imported before research training can begin.
- The current Colab runtime uses Python 3.13. Training requirements now select TensorFlow 2.20 there,
  while retaining TensorFlow 2.19.1 for Python 3.11/3.12.

## User exports and frozen snapshot — 2026-09-27

- User supplied unchanged adjusted/unadjusted pytse full-history exports: 4,231 observations each,
  2007-03-11 through 2026-09-26. Source exporter retrieval time/package version were not recorded.
- Five-year snapshot: 2021-09-26 through 2026-09-26, 1,038 observations.
- Independently reconstructed adjusted price fields agree with provided rounded prices within 0.5 rial.
  Date coverage, volume/value/count agreement, and Jalali date conversion pass.
- One invalid opening price (zero), 2025-07-29, quarantined. Its valid official-close adjustment reference
  remains in the full basis; windows/targets crossing the excluded session are removed.
- 1,037 cleaned candles; 1,004 feature rows after 33 warm-up exclusions.
- 27 implementation tests pass. Real training/evaluation status is recorded after Colab completion.
- Colab allocated NVIDIA A100-SXM4-80GB, with approximately 167 GB host RAM; Drive is mounted.

## Completed Colab experiment — 2026-09-27

- Training source commit: `20092ec` (full commit stored with artifacts), run fingerprint `0fae8c8d8bf0`.
- Guided notebook completed all eight code cells in a fresh isolated Python kernel on Colab.
  Drive was mounted interactively in the fresh runtime; the isolated kernel reused that mount.
  An executed notebook with outputs is saved separately in the project Drive folder.
- 48 features; common target dates: 618 training, 132 validation, 134 test forecasts.
  Training ends 2024-11-06; validation 2024-11-09–2025-06-08; test 2025-06-09–2026-09-26.
- All six length/width trials completed with early stopping, plus the OHLCV ablation.
  Epoch counts: 25/16 for length 10, 22/14 for length 30, 22/14 for length 60 (32/64 units);
  OHLCV ablation 29 epochs. Selection uses validation only: length 60, units 64, RMSE 324.054 rial.
- TensorFlow 2.20 detects a GPU. Both `.keras` and `.h5` reload checks reproduce exported predictions.
- All seven deliverables exist, including the English report and portable checksummed archive.

| Model | Test MAE (adjusted rial) | Test RMSE (adjusted rial) | Test MAPE (%) |
|---|---:|---:|---:|
| Engineered LSTM | 335.574 | 467.071 | 11.756 |
| Persistence | 52.125 | 60.801 | 1.966 |
| Ridge | 187.942 | 261.746 | 7.000 |
| OHLCV LSTM | 283.325 | 390.777 | 9.900 |

Persistence wins this held-out comparison. The LSTM does not demonstrate an advantage, and engineered
features do not improve on the OHLCV ablation here. No further tuning follows test inspection.
These are retrospective adjusted-price research results, with the limitations described in the report.

