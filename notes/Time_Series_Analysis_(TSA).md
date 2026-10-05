# Time Series & Time Series Analysis — Beginner Notes

Your keywords are mostly correct. One correction first:

> **Variation is usually called _Irregular Variation_, _Random Variation_, or _Noise_ — not “Regularity.”**

A useful mental model is:

$$
\boxed{\text{Time Series} = \text{Trend} + \text{Seasonality} + \text{Cycle} + \text{Noise}}
$$

The exact mathematical relationship can sometimes be additive or multiplicative, which we'll cover below.

---

# 1. What is a Time Series?

A **time series** is a sequence of observations recorded in **time order**.

For example:

| Date  | Stock Price |
| ----- | ----------: |
| Day 1 |         100 |
| Day 2 |         103 |
| Day 3 |         101 |
| Day 4 |         106 |
| Day 5 |         108 |

The important difference between ordinary tabular data and time-series data is that **order matters**.

In ordinary regression, rows can often be shuffled without changing the problem.

In time series:

$$
Y_t \neq \text{independent of }Y_{t-1}
$$

Yesterday's value may contain information about today's value.

Examples of time series include:

- stock prices
- exchange rates
- monthly sales
- electricity consumption
- temperature
- website traffic
- unemployment
- GDP
- product demand
- hospital admissions
- machine sensor measurements

---

# 2. Time Series Analysis vs. Forecasting

These two concepts are related but not identical.

### Time Series Analysis

The goal is to **understand the structure and behavior** of data over time.

Questions might include:

- Is sales demand increasing?
- Is there a seasonal pattern?
- Are weekends different from weekdays?
- Does the current value depend strongly on yesterday's value?
- Is there a long-term economic cycle?
- Are there unusual observations?

### Time Series Forecasting

The goal is to use past observations to **predict future observations**.

For example:

```text
Historical data

2021 → 100
2022 → 110
2023 → 125
2024 → 138
2025 → 150

             ↓
       Forecasting Model

             ↓

2026 → ?
2027 → ?
```

So:

$$
\boxed{\text{Analysis} \rightarrow \text{Understand}}
$$

$$
\boxed{\text{Forecasting} \rightarrow \text{Predict}}
$$

---

# 3. Components of a Time Series

A classical time series is often described using four components:

$$
\boxed{T + S + C + I}
$$

where:

- $T$ = Trend
- $S$ = Seasonality
- $C$ = Cycle
- $I$ = Irregular/Noise

---

## 3.1 Trend

A **trend** is the long-term direction of the series.

There are three simple possibilities:

### Upward Trend

Values generally increase over time.

```text
Value
  |
  |                 *
  |             *
  |          *
  |      *
  |   *
  +-------------------- Time
```

Examples:

- population growth
- long-term company revenue growth
- increasing electricity demand

### Downward Trend

```text
Value
  |
  | *
  |    *
  |       *
  |           *
  |               *
  +-------------------- Time
```

Examples:

- demand for an obsolete product
- declining production
- decreasing costs caused by technological improvement

### Flat / No Trend

```text
Value
  |
  |   *  *     *
  | *      *      *
  |      *    *
  +-------------------- Time
```

The values fluctuate, but there is no obvious long-term direction.

### Important

A trend does **not** mean:

> "Every observation is higher than the previous observation."

For example:

```text
100 → 105 → 103 → 110 → 108 → 117
```

There are decreases, but the **overall direction is upward**.

---

# 4. Seasonality

**Seasonality** is a pattern that repeats at a **known and relatively fixed interval**.

Examples:

### Monthly sales

Ice cream sales might increase every summer:

```text
2023: Low → Medium → High → Medium → Low
2024: Low → Medium → High → Medium → Low
2025: Low → Medium → High → Medium → Low
```

The pattern repeats approximately every **12 months**.

### Other examples

Daily seasonality:

$$
\text{Period}=24\text{ hours}
$$

Weekly seasonality:

$$
\text{Period}=7\text{ days}
$$

Monthly data with yearly seasonality:

$$
\text{Period}=12
$$

Quarterly data:

$$
\text{Period}=4
$$

Examples:

- restaurant demand by day of week
- electricity usage by hour
- tourism by month
- retail sales around Christmas
- traffic during rush hour

So the key property of seasonality is:

$$
\boxed{\text{Pattern repeats at predictable intervals}}
$$

---

# 5. Cycle

A **cycle** is also an upward/downward pattern, but unlike seasonality, its timing is usually **not fixed**.

This distinction is very important.

| Seasonality              | Cycle                            |
| ------------------------ | -------------------------------- |
| Fixed/repeating interval | No exact fixed interval          |
| Usually shorter          | Often longer                     |
| Predictable timing       | Timing may vary                  |
| Example: summer sales    | Example: economic boom/recession |

For example, an economy might experience:

```text
Growth
   ↓
Peak
   ↓
Recession
   ↓
Recovery
   ↓
Growth
```

But the business cycle doesn't necessarily repeat every:

- 4 years
- 5 years
- 10 years

with exact regularity.

Therefore:

$$
\boxed{\text{Seasonality = periodic}}
$$

while

$$
\boxed{\text{Cycle = longer-term oscillation without a fixed period}}
$$

---

# 6. Irregular Variation / Noise

Noise represents unpredictable fluctuations that cannot easily be explained by:

- trend
- seasonality
- cycle

For example:

```text
Expected sales = 1,000

Actual sales:

995
1012
987
1007
1022
```

Some variation is simply random.

We can write:

$$
Y_t = \text{systematic components} + \text{noise}
$$

where the noise is commonly denoted:

$$
\epsilon_t
$$

Ideally:

$$
E(\epsilon_t) \approx 0
$$

A good forecasting model tries to capture the **predictable structure** while leaving unpredictable variation as residual noise.

---

# 7. Putting the Components Together

Suppose monthly ice cream sales behave like this:

```text
Long-term growth          → Trend
Summer sales spike        → Seasonality
Economic recession        → Cycle
Random weather/event      → Noise
```

All four can exist simultaneously.

---

# 8. Additive vs. Multiplicative Time Series

There are two common ways to think about these components.

## Additive Model

$$
\boxed{Y_t=T_t+S_t+C_t+I_t}
$$

Useful when seasonal fluctuations stay roughly the **same size**.

For example:

```text
Sales = Trend + 500-unit seasonal effect
```

regardless of whether average sales are 5,000 or 20,000.

---

## Multiplicative Model

$$
\boxed{Y_t=T_t\times S_t\times C_t\times I_t}
$$

Useful when seasonal fluctuations become larger as the series grows.

For example:

```text
2010: average = 1,000
seasonal swing ≈ 100

2025: average = 10,000
seasonal swing ≈ 1,000
```

The seasonal effect is more like a **percentage** of the level.

---

# 9. Lag — One of the Most Important TSA Concepts

A **lag** means looking backward in time.

Suppose:

$$
Y_t
$$

is today's price.

Then:

$$
Y_{t-1}
$$

is yesterday's price.

$$
Y_{t-2}
$$

is two days ago.

For example:

| Day | $Y_t$ | $Y_{t-1}$ |
| --- | ----: | --------: |
| 1   |   100 |         — |
| 2   |   105 |       100 |
| 3   |   107 |       105 |
| 4   |   103 |       107 |

This becomes extremely important when you reach **ARIMA**.

---

# 10. Autocorrelation

Ordinary correlation asks:

> Are $X$ and $Y$ related?

**Autocorrelation** asks:

> Is a time series correlated with its own previous values?

For example:

$$
Corr(Y_t,Y_{t-1})
$$

If today's stock value is strongly related to yesterday's value, lag-1 autocorrelation may be high.

You will later encounter two important plots:

- **ACF** — Autocorrelation Function
- **PACF** — Partial Autocorrelation Function

These are especially useful when studying ARIMA.

---

# 11. Stationarity

This is one of the most important concepts to learn before ARIMA.

A time series is roughly **stationary** when its statistical behavior doesn't systematically change over time.

For example, approximately stable:

- mean
- variance
- autocorrelation structure

A stationary-looking series might fluctuate around:

$$
\mu=100
$$

like:

```text
98
102
96
105
101
97
103
```

But consider:

```text
10
20
30
40
50
60
70
```

The mean clearly changes with time.

Therefore this series has a trend and is **not stationary**.

Why does this matter?

Traditional ARIMA generally works with a stationary series, which is why ARIMA contains the **I — Integrated** component.

---

# 12. Forecasting Models

Your tutorial mentions two major families:

1. **ARIMA**
2. **Exponential Smoothing**

These are classic statistical forecasting methods.

---

# 13. ARIMA

ARIMA stands for:

$$
\boxed{\text{Auto-Regressive Integrated Moving Average}}
$$

or:

$$
\boxed{AR + I + MA}
$$

An ARIMA model is represented as:

$$
\boxed{ARIMA(p,d,q)}
$$

Each parameter has a different meaning.

---

# 14. AR — AutoRegressive

AR means:

> Predict the current observation using previous observations.

For example:

$$
Y_t=c+\phi_1Y_{t-1}+\epsilon_t
$$

This says:

> Today's value depends partly on yesterday's value.

For example:

```text
Tomorrow's sales
    ↓
Today's sales
    ↓
Yesterday's sales
```

If we use the previous two observations:

$$
Y_t=c+\phi_1Y_{t-1}+\phi_2Y_{t-2}+\epsilon_t
$$

we have an:

$$
AR(2)
$$

model.

The ARIMA parameter:

$$
p
$$

represents the **AR order**.

So:

```text
p = number of autoregressive lags
```

---

# 15. I — Integrated

The **I** part is about **differencing**.

It is generally used to help transform a non-stationary series into a stationary one.

Suppose:

```text
100
105
111
118
126
```

Instead of modeling those values directly, calculate the differences:

$$
Y_t-Y_{t-1}
$$

giving:

```text
5
6
7
8
```

This operation is called:

$$
\boxed{\text{Differencing}}
$$

One round of differencing means:

$$
d=1
$$

No differencing:

$$
d=0
$$

Two rounds:

$$
d=2
$$

Thus:

$$
d=\text{order of differencing}
$$

---

# 16. MA — Moving Average

This terminology can be confusing.

The **MA in ARIMA does not simply mean taking a rolling average of observations.**

Instead, it models the current value using previous **forecast errors**.

Conceptually:

$$
Y_t=\mu+\epsilon_t+\theta_1\epsilon_{t-1}
$$

where:

$$
\epsilon_{t-1}
$$

is the previous prediction error.

If yesterday's model made a significant error, today's prediction can account for it.

The ARIMA parameter:

$$
q
$$

specifies the number of lagged errors included.

---

# 17. ARIMA(p,d,q)

Now the whole notation makes sense:

$$
\boxed{ARIMA(p,d,q)}
$$

| Parameter | Meaning                 |
| --------- | ----------------------- |
| $p$       | Number of AR lags       |
| $d$       | Number of differences   |
| $q$       | Number of MA error lags |

For example:

$$
ARIMA(2,1,1)
$$

approximately means:

> Use two past observations, difference the series once, and use one previous forecast error.

---

# 18. ARIMA Family

You'll eventually encounter several related models.

### AR

$$
ARIMA(p,0,0)
$$

### MA

$$
ARIMA(0,0,q)
$$

### ARMA

$$
ARIMA(p,0,q)
$$

### ARIMA

$$
ARIMA(p,d,q)
$$

### SARIMA

Used when the time series contains **seasonality**.

It extends ARIMA with seasonal parameters:

$$
SARIMA(p,d,q)(P,D,Q)_s
$$

Don't worry about SARIMA yet. First understand ARIMA thoroughly.

---

# 19. Exponential Smoothing

Exponential smoothing takes another approach.

The basic idea is:

> Recent observations should generally have more influence on the forecast than very old observations.

For example:

```text
Yesterday       → High importance
2 days ago      → Less
3 days ago      → Less
4 days ago      → Even less
...
```

The importance decreases exponentially.

---

# 20. Simple Exponential Smoothing

A basic exponential smoothing equation is:

$$
F_{t+1}=\alpha Y_t+(1-\alpha)F_t
$$

where:

- $Y_t$ = actual observation
- $F_t$ = previous forecast
- $F_{t+1}$ = new forecast
- $\alpha$ = smoothing parameter

with:

$$
0\leq\alpha\leq1
$$

---

## Large Alpha

For example:

$$
\alpha=0.9
$$

Recent observations receive a lot of importance.

The model responds **quickly** to changes.

---

## Small Alpha

For example:

$$
\alpha=0.1
$$

Past information receives more influence.

The resulting forecast is **smoother** and responds more slowly.

---

# 21. Exponential Smoothing Family

There are three particularly important variants.

### Simple Exponential Smoothing

For data with:

- no significant trend
- no seasonality

```text
Level only
```

---

### Holt's Method

For:

- level
- trend

```text
Level
+
Trend
```

---

### Holt-Winters Method

For:

- level
- trend
- seasonality

```text
Level
+
Trend
+
Seasonality
```

So a useful hierarchy is:

```text
Exponential Smoothing
│
├── Simple Exponential Smoothing
│      └── Level
│
├── Holt
│      ├── Level
│      └── Trend
│
└── Holt-Winters
       ├── Level
       ├── Trend
       └── Seasonality
```

---

# 22. ARIMA vs. Exponential Smoothing

At beginner level, think about the distinction this way:

| ARIMA                        | Exponential Smoothing                    |
| ---------------------------- | ---------------------------------------- |
| Models autocorrelation       | Models evolving level/trend/seasonality  |
| Uses lag relationships       | Gives more weight to recent observations |
| AR + differencing + errors   | Smoothing equations                      |
| Stationarity is important    | Components are emphasized                |
| Strong statistical framework | Often intuitive for demand forecasting   |

Neither model is universally superior.

Performance depends on:

- the dataset
- forecast horizon
- seasonality
- trend
- structural changes
- parameter selection

---

# 23. What About Machine Learning?

Classical time-series forecasting includes methods such as:

```text
Simple Moving Average
        ↓
Exponential Smoothing
        ↓
Holt / Holt-Winters
        ↓
AR / MA / ARIMA
        ↓
SARIMA
```

You can then move toward machine learning:

```text
Linear Regression
Random Forest
XGBoost
```

and deep learning:

```text
RNN
LSTM
GRU
Transformers
```

Since you're working with market forecasting, this distinction is useful:

$$
\boxed{\text{ARIMA is statistical forecasting}}
$$

whereas

$$
\boxed{\text{LSTM is deep-learning-based forecasting}}
$$

They solve similar forecasting problems using fundamentally different approaches.

---

# 24. Time-Series Data in Pandas

Pandas is one of the core Python libraries for handling time series.

For example:

```python
import pandas as pd

df = pd.read_csv("data.csv")

df["Date"] = pd.to_datetime(df["Date"])

df = df.set_index("Date")

print(df.head())
```

You might obtain:

```text
            Price
Date
2026-01-01   100
2026-01-02   103
2026-01-03   101
2026-01-04   106
```

A key concept is making the date a proper:

```python
DatetimeIndex
```

rather than storing dates as ordinary strings.

---

# 25. Plotting the Series

Matplotlib lets you inspect the series visually.

```python
import matplotlib.pyplot as plt

plt.plot(df.index, df["Price"])

plt.xlabel("Date")
plt.ylabel("Price")
plt.title("Price Over Time")

plt.show()
```

Visual inspection is usually one of the **first steps** in time-series analysis.

You're looking for:

- trend
- seasonality
- unusual observations
- sudden structural changes
- volatility
- missing values

---

# 26. Pandas Rolling Statistics

You can calculate a moving average:

```python
df["MA_7"] = df["Price"].rolling(window=7).mean()
```

For example:

```text
Original:

100
105
90
110
95
108
102
```

The moving average smooths some of the noise.

Then:

```python
plt.plot(df["Price"], label="Original")
plt.plot(df["MA_7"], label="7-Day Moving Average")

plt.legend()
plt.show()
```

This makes trends easier to inspect.

---

# 27. Important Correction About Python Libraries

Your notes say:

> Python: Pandas + Matplotlib

Those are excellent for **data preparation and visualization**, but you'll normally need another library to actually build ARIMA and exponential-smoothing models:

### Pandas

Data manipulation:

```python
import pandas as pd
```

### Matplotlib

Visualization:

```python
import matplotlib.pyplot as plt
```

### Statsmodels

Classical statistical time-series models:

```python
from statsmodels.tsa.arima.model import ARIMA
```

and:

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing
```

So a more complete toolkit is:

$$
\boxed{\text{Pandas + Matplotlib + Statsmodels}}
$$

Later you may also encounter:

- NumPy
- SciPy
- scikit-learn
- pmdarima
- Prophet
- PyTorch
- TensorFlow

---

# 28. Train/Test Split Is Different in Time Series

Suppose you have observations from 2020–2026.

In normal ML, you might randomly shuffle data before splitting it.

That is usually **wrong for time-series forecasting**.

You should preserve chronological order:

```text
2020 ─────────────── 2025 | 2026
         TRAIN            TEST
```

not:

```text
2020 2024 2022 → Train
2021 2026 2023 → Test   ✗
```

because using future observations to predict the past creates:

$$
\boxed{\text{Data Leakage}}
$$

This is one of the most important practical rules in time-series modeling.

---

# 29. Forecast Horizon

The **forecast horizon** tells us how far into the future we're predicting.

For example:

### One-step forecasting

$$
t+1
$$

Predict tomorrow.

### Multi-step forecasting

$$
t+1,t+2,\ldots,t+30
$$

Predict the next 30 days.

Generally:

$$
\text{Longer forecast horizon}
\Rightarrow
\text{greater uncertainty}
$$

---

# 30. Forecast Errors

Suppose:

$$
Actual=110
$$

and:

$$
Forecast=105
$$

Then forecast error can be written as:

$$
e_t=Y_t-\hat Y_t
$$

Therefore:

$$
e_t=110-105=5
$$

A good model should ideally produce residuals that look largely like random noise.

If residuals still contain obvious patterns, that often means:

> The model failed to capture some useful information.

---

# 31. Forecast Evaluation Metrics

You'll frequently encounter:

### MAE

Mean Absolute Error:

$$
MAE=\frac{1}{n}\sum|y_t-\hat y_t|
$$

Easy interpretation:

> On average, how far are predictions from reality?

Lower is better.

---

### MSE

Mean Squared Error:

$$
MSE=\frac{1}{n}\sum(y_t-\hat y_t)^2
$$

Large errors receive stronger penalties.

Lower is better.

---

### RMSE

$$
RMSE=
\sqrt{
\frac{1}{n}
\sum
(y_t-\hat y_t)^2
}
$$

Useful because its units are the same as the original variable.

Again:

$$
\boxed{\text{Lower is better}}
$$

---

### MAPE

Mean Absolute Percentage Error:

$$
MAPE=
\frac{100}{n}
\sum
\left|
\frac{y_t-\hat y_t}{y_t}
\right|
$$

For example:

$$
MAPE=5\%
$$

roughly means an average absolute percentage error of 5%.

But MAPE can behave poorly when actual values are zero or very close to zero.

---

# 32. Typical Time-Series Analysis Workflow

This is probably the most useful framework to remember.

```text
1. Collect Data
       ↓
2. Convert Date/Time Properly
       ↓
3. Sort Chronologically
       ↓
4. Clean Missing / Invalid Data
       ↓
5. Plot the Series
       ↓
6. Identify Components
       ├── Trend?
       ├── Seasonality?
       ├── Cycle?
       └── Noise?
       ↓
7. Explore Lag Relationships
       ↓
8. Check Stationarity
       ↓
9. Split Train / Test Chronologically
       ↓
10. Choose Forecasting Model
       ├── Exponential Smoothing
       ├── ARIMA
       ├── SARIMA
       ├── ML
       └── Deep Learning
       ↓
11. Train Model
       ↓
12. Forecast Test Period
       ↓
13. Evaluate
       ├── MAE
       ├── MSE
       ├── RMSE
       └── MAPE
       ↓
14. Analyze Residuals
       ↓
15. Forecast Future Values
```

This is a much better mental model than thinking:

> "Load data → train ARIMA → predict."

Most of the real work happens **before and after fitting the model**.

---

# 33. A Small Example

Suppose you have monthly sales:

```text
2023:
100 110 130 150 180 220 250 240 190 160 130 120

2024:
110 120 140 165 195 240 270 260 210 175 145 130

2025:
120 130 155 180 210 260 290 280 225 190 155 140
```

We can already identify:

### Trend

Sales are generally growing each year.

$$
T \uparrow
$$

### Seasonality

Sales increase around the middle of every year.

$$
S=\text{12-month pattern}
$$

### Cycle

There might be a broader economic cycle, but three years of data may not be enough to identify it reliably.

### Noise

Individual months will have unexplained deviations.

A possible model would therefore need to account for:

$$
\boxed{\text{Trend + Seasonality}}
$$

making something like Holt-Winters or SARIMA more appropriate than plain simple exponential smoothing.

---

# 34. The Big Picture

You can organize everything you've learned into this map:

```text
TIME SERIES
│
├── Analysis
│   │
│   ├── Components
│   │   ├── Trend
│   │   ├── Seasonality
│   │   ├── Cycle
│   │   └── Irregular / Noise
│   │
│   ├── Lag
│   ├── Autocorrelation
│   └── Stationarity
│
├── Forecasting
│   │
│   ├── Statistical Methods
│   │   │
│   │   ├── Exponential Smoothing
│   │   │   ├── Simple
│   │   │   ├── Holt
│   │   │   └── Holt-Winters
│   │   │
│   │   └── ARIMA
│   │       ├── AR → Past values
│   │       ├── I  → Differencing
│   │       └── MA → Past errors
│   │
│   ├── Machine Learning
│   │   ├── Linear Regression
│   │   ├── Random Forest
│   │   └── XGBoost
│   │
│   └── Deep Learning
│       ├── RNN
│       ├── LSTM
│       ├── GRU
│       └── Transformer
│
└── Python
    ├── Pandas → Data
    ├── Matplotlib → Visualization
    ├── Statsmodels → ARIMA / ETS
    ├── Scikit-learn → ML
    └── PyTorch / TensorFlow → Deep Learning
```

---

# 35. What I Recommend Learning Next

Given that you're currently working on a **market-forecasting project**, I'd learn TSA in this order:

1. **Datetime data in Pandas**
2. **Trend, Seasonality, Cycle, Noise**
3. **Moving averages**
4. **Lag and autocorrelation**
5. **Stationarity**
6. **Differencing**
7. **ACF and PACF**
8. **Simple Exponential Smoothing**
9. **Holt**
10. **Holt-Winters**
11. **AR and MA**
12. **ARIMA**
13. **SARIMA**
14. **Time-series train/test validation**
15. **MAE, RMSE, MAPE**
16. **Compare statistical models against a naive baseline**
17. Then move to **LSTM/GRU/XGBoost**

The particularly important point for your current learning path is **not to jump directly from “time-series components” to LSTM**. Understanding **lags, autocorrelation, stationarity, differencing, residuals, and baseline forecasting** will make the behavior of your Market-Forecast project much easier to interpret later.
