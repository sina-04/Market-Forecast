# MarketForecast research report

## Objective and data
Predict فولاد's next observed traded session's adjusted official closing price after the current session.
Source: TSETMC via user-supplied pytse-client CSV exports. Period: 2021-09-26 to 2026-09-26.
Retrieved: Not recorded by source exporter. Instrument IDs: 46348559193224090.
Prices are rials; volume is shares. The raw source, normalized raw CSV, and SHA-256 checksums are frozen.
Official closing price is pClosing (FinPy Final); pDrCotVal (FinPy Close) is last trade.

## Cleaning and corporate actions
1038 raw rows; 1037 valid rows;
1 quarantined rows. Reasons: {'nonpositive_price': 1, 'invalid_candle': 1}.
Adjustment basis: Verified complete export chain, including quarantined missing-open session.
Quarantined candles are excluded; all input windows and their targets must be consecutive source sessions.
User CSV imports preserve original export bytes; HTTP response bodies and original retrieval/package
version metadata are unavailable when the exporter did not record them (see snapshot manifest).
No synthetic holiday/suspension candles or price interpolation. Large raw moves are flagged, not automatically removed.
Backward adjustment multiplies price fields by the reverse cumulative product of next-session
previous official close / current official close. Final factor = 1. Volume is unchanged.
This uses future corporate-action information: the study is retrospective on a frozen adjustment basis,
not a point-in-time backtest, forecast of unadjusted transaction prices, or evidence of achievable profit.

## Features and chronological preparation
1004 usable feature rows after 33 warm-up/nonfinite exclusions.
Features include OHLCV, lags, returns, SMA/EMA 5/10/20, volatility/extrema, Wilder RSI-14 and ATR-14,
MACD 12/26/9, Bollinger 20, volume ratios, interaction and calendar variables.
All rolling calculations use current/past observations only, on the fixed adjusted series.
Common eligible target dates are shared by all window lengths. Split fractions are
70% / 15% / 15%.
Cutoffs: {'train': {'first_target': '2022-02-07', 'last_target': '2024-11-06', 'samples': 618}, 'validation': {'first_target': '2024-11-09', 'last_target': '2025-06-08', 'samples': 132}, 'test': {'first_target': '2025-06-09', 'last_target': '2026-09-26', 'samples': 134}}.
Input and target StandardScalers are fitted independently on training inputs/targets only.

## Models and selection
One LSTM layer; dropout 0.2; dense linear output; Adam 0.001; MSE loss;
batch size 32; at most 100 epochs; early stopping patience 10.
Validation-only search: lengths [10, 30, 60], units [32, 64].
Selected: length 60, units 64, validation RMSE 324.054 adjusted rials.
Seed: 42. Ridge alpha is selected on validation. OHLCV ablation uses the selected architecture.
The test set is evaluated only after all selections; no train-plus-validation refit.

## Held-out results
MAE and RMSE are adjusted rials; MAPE is percent. MSE is also recorded in test_metrics.json.

| Model | MAE | RMSE | MAPE (%) |
|---|---:|---:|---:|
| lstm | 335.574 | 467.071 | 11.756 |
| persistence | 52.125 | 60.801 | 1.966 |
| ridge | 187.942 | 261.746 | 7.000 |
| ohlcv_lstm | 283.325 | 390.777 | 9.900 |

LSTM test RMSE improvement against persistence: -668.20% (negative means worse).
The result is descriptive; performance is not guaranteed on later market regimes.
Five years of one stock provide limited independent samples, and overlapping windows are correlated.
The study does not include transaction costs, tradability/queues, or a trading strategy.

## Reproducibility and artifacts
The environment, configuration, snapshot checksums, feature order, split dates, scalers,
candidate logs, selected .keras/.h5 models, sequences, predictions, metrics, and figures are saved together.
Both selected saved model formats were reloaded and verified against exported predictions.
See loss_selected_lstm.png, loss_ohlcv_lstm.png, test_forecasts.png, and residuals.png.


## Interpretation and independent reload
The engineered LSTM does not improve on persistence or the OHLCV-only LSTM on these held-out dates. Its RMSE is 7.68 times persistence RMSE. The forecast plot shows substantial underprediction in later test sessions; the experiment does not establish a predictive advantage. No further tuning was performed after viewing the test results. A fresh Python kernel reloaded both model formats and the saved scalers and reproduced all 134 exported forecasts. Hardware: NVIDIA A100-SXM4-80GB.
