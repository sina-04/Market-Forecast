# Data and model contract

Forecast after t completes: input t-L+1 through t; target adjusted official close at the next observed
actual-trade session. No calendar-day extrapolation or holiday interpolation.

## Normalized fields and adjustment

`date`, `jalali_date`, `instrument_id`, `open`, `high`, `low`, `official_close`, `last_trade`,
`previous_official_close`, `volume`, `value`, `trade_count`. Cleaned data also stores adjusted fields,
adjustment factor/event, large-jump flag, elapsed days, and session number.

Exact normalized ticker and company identity are both required. Historical exact-symbol instrument IDs
are retained. Identical records collapse; conflicting dates are quarantined. Source JSON preserves all
fetched data; the raw CSV covers the requested five-year interval.

Let C_t be raw official close and Y_(t+1) next-session previous official close.
Set r_t=Y_(t+1)/C_t, r_T=1, factor_t=product(r_t ... r_T). Multiply prices by factor_t;
never adjust volume. Retain float precision. This uses future information and is retrospective.
Invalid traded records stop preparation after saving an audit. Frozen CSV edits invalidate checksums;
reviewed repairs require a new snapshot with preserved original source and documented provenance.

## Features and splits

Close/return lags 1/2/5; rolling windows 5/10/20; Wilder RSI/ATR 14 with a simple-average seed;
MACD 12/26/9; Bollinger 20 with two sample standard deviations. Flat RSI=50; gain-only RSI=100;
flat Bollinger position=0. Other zero denominators become missing. Warm-up/nonfinite rows are audited.
Sequences cannot bridge excluded feature rows. Weekday/Jalali month are cyclic, Gregorian calendar
month-end is known at forecast time. Last observed session of the month is not a causal feature.

Common eligible targets start after 60 observations and split 70/15/15. Feature scalers fit unique
training input rows; target scalers fit training labels. Earlier context may enter later split windows.
Select lengths 10/30/60 × widths 32/64 by validation RMSE in adjusted rials. No validation refit.
Ridge uses the selected flattened window with validation-selected alpha 0.1/1/10.
OHLCV ablation uses the selected length/width with separate scalers. No improvement is guaranteed.

## Reliability and limits

HTTPS validation stays enabled; requests have bounded timeouts/attempts. Malformed schemas fail.
Today is excluded. Snapshot manifests are atomic and contain SHA-256 checksums.
Run fingerprints include configuration, data hashes, and Python source hashes. Seeds/environment/devices
are recorded; floating-point behavior may vary across hardware.
Feature-causality tests hold the backward adjustment basis fixed. Point-in-time deployment would need
dated corporate-action data and a different evaluation design. No trading strategy or profit claim is made.

