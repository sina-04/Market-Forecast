# Foolad hourly forecasting experiment

Predict the next observed traded bar's adjusted last traded price after the current bar completes.
Period: 2021-10-02 09:00:00 through 2026-09-30 12:00:00. Source: User pytse-client hourly bars aggregated from returned trades.
One-hour, left-labelled aggregation; a timestamp identifies the start of its completed bar.
The next observed bar may follow overnight/weekend gaps. This is a different horizon and target from
the previous daily official-close experiment; their raw errors are not a like-for-like improvement measure.

## Data and adjustment
4273 valid hourly bars. 15 unresolved dates.
Raw returned-trade aggregation verification and source hashes are recorded in the snapshot.
No missing-bar interpolation. All returned hours are retained, including
236 bars at/after 13:00; source session-hour classification is unverified.
Daily official-close action coefficients are applied uniformly to every bar in each day, never
inferred from hourly last prices. This is a fixed retrospective adjustment, not a point-in-time backtest.
Timezone basis: Naive exchange-local timestamps from exporter; no timezone conversion. Prices are adjusted rials, volumes are returned shares.

## Features and splits
4009 usable feature bars. Indicators restart after unresolved dates.
All candidate windows/targets exclude crossings of known missing days. Periods count observed bars.
Inputs include relative OHLC, returns/lags, normalized rolling indicators, log/relative volume,
hour-of-day and calendar features, and elapsed hours. Hourly labels are full timestamps.
Training-only scalers; chronological 70/15/15 common targets across candidate lengths.
Cutoffs: {'train': {'first_target': '2021-11-03 12:00:00', 'last_target': '2024-09-01 11:00:00', 'samples': 2490}, 'validation': {'first_target': '2024-09-01 12:00:00', 'last_target': '2025-05-03 12:00:00', 'samples': 533}, 'test': {'first_target': '2025-05-04 09:00:00', 'last_target': '2026-09-30 12:00:00', 'samples': 535}}.

## Training and selection
One LSTM, dropout 0.2, Adam 0.001, MSE;
batch 64, up to 100 epochs, patience 12.
Target mode: log_return. Log-return predictions reconstruct price from the prior
observed adjusted last price, giving zero predicted return the persistence forecast.
Validation-only search: [12, 24, 60] observed bars × [32, 64] units.
Selected lstm_60_32; validation RMSE 29.210 adjusted rials.
Ridge alpha selected on validation; OHLCV ablation uses the selected architecture and common timestamps.
Test targets are evaluated only after selection. Seed 42. A100 enforced and recorded in environment.json.

## Held-out hourly results
MAE/RMSE in adjusted rials; MAPE in percent; MSE recorded in test_metrics.json.

| Model | MAE | RMSE | MAPE (%) |
|---|---:|---:|---:|
| lstm | 22.646 | 33.049 | 0.935 |
| persistence | 20.322 | 32.793 | 0.832 |
| ridge | 52.373 | 99.132 | 2.149 |
| ohlcv_lstm | 22.452 | 32.143 | 0.923 |

LSTM test RMSE improvement against persistence: -0.78% (negative means worse).
More hourly bars do not guarantee better accuracy; overlapping samples are correlated.
There is no trading strategy, transaction-cost model, or profit claim.

## Reproducibility
Snapshot, configuration, sources, environment/GPU identity, timestamp splits, scalers, candidate logs,
selected .keras/.h5 models, predictions, metrics and plots are saved. Both model formats reload and
reproduce the exported predictions. The bundle retains raw-trade hashes; the original raw-trade cache
remains in the local exports folder.
