# Financial Market Price Forecasting with LSTM and Feature Engineering

## Source and scope

- **Source:** [GoalEarn task sheet — “Project2 - Marjan Jalali”](https://docs.google.com/spreadsheets/d/1gE5eWWF8Opc3QNSFNKndOc7-LU7XZrlOsMVtn3eAGAY/edit?gid=291802658#gid=291802658)
- **Task title:** Forecast prices in a financial market using LSTM and feature engineering.
- **Task goal:** The sheet has a “Task Goal” heading but no separate goal statement. The title and steps describe forecasting the next day's price or return for a selected asset.
- **Start and end dates:** Not supplied in the sheet.
- **Order:** Follow the populated steps below in sequence. Docker study is optional if time remains.

## 1. Select a market, asset, and timeframe

Choose the target market: stocks (the Iranian exchange, NYSE, or NASDAQ), cryptocurrencies (such as Bitcoin or Ethereum), forex (such as EUR/USD or GBP/USD), or commodities and indices (such as gold, oil, or the S&P 500). Select the asset or symbol; examples in the sheet are BTC-USD, AAPL, GSPC for the S&P 500, and XAUUSD for gold. Choose the observation interval, such as daily, hourly, or minute-level data. **The sheet recommends daily data for this project.**

**Knowledge needed:** Types of financial markets; open and close prices, trading volume, volatility, and candlesticks; financial time series; and the meaning and uses of daily, hourly, and weekly intervals.

**Resources from the sheet:** [1](https://www.youtube.com/watch?v=VWCKgHkjBIc) · [2](https://www.aparat.com/v/vov6r57) · [3](https://www.investopedia.com/trading/candlestick-charting-what-is-it/) · [4](https://nobitex.ir/mag/candlestick/) · [5](https://www.youtube.com/watch?v=74rDhJexmTg) · [6](https://www.youtube.com/watch?v=JtXZjlzDWZM)

## 2. Collect data

Collect at least **three to five years of daily historical data** for the chosen asset. The sheet recommends a sufficiently large dataset so the model has a chance to learn patterns and suggests Yahoo Finance as one source. Other listed sources are Binance Kline data for cryptocurrencies and TSETMC or Rahavard 365 for Iranian stocks. Use Python and pandas to load, inspect, and check the data.

**Knowledge needed:** Financial data sources, including Yahoo Finance, TSE, Binance, and Alpha Vantage; Python and pandas.

**Resources from the sheet:** [1](https://www.youtube.com/watch?v=CeCIRXHcmRA) · [2](https://www.youtube.com/watch?v=7tPfWqQi77o) · **Link 3: no URL in the sheet** · [4](https://aroussi.com/post/python-yahoo-finance)

## 3. Clean and save the data

1. Sort observations chronologically, convert the date column to a datetime type, and set it as the index.
2. Find missing values (`NaN`) and decide whether to remove or replace them.
3. Inspect abnormal price jumps and invalid candles, such as `High < Low` or a price of zero; correct or remove clearly erroneous records.
4. Find duplicate rows and remove duplicate observations for the same date.
5. Convert numeric fields to appropriate `float` or `int` types. Remove extra characters, such as commas in volume fields, before conversion.
6. Inspect volume for invalid or suspicious values, including negative volume and zero or unusually low volume on nonholiday trading days.
7. Save the cleaned dataset as a `.csv` file, for example with `df.to_csv()`.

**Knowledge needed:** Chronological ordering of financial time series; OHLCV data; missing values, outliers, and duplicates; CSV structure; Python and pandas for cleaning.

**Resources from the sheet:** [1](https://www.youtube.com/watch?v=SXZBaTPe9BU) · [2](https://www.youtube.com/watch?v=ai_rWJeLkss)

## 4. Engineer features

Turn raw **Open, High, Low, Close, and Volume (OHLCV)** observations into meaningful model inputs. The sheet lists these groups:

- **Basic features:** Lagged values and daily returns, to represent recent prices and relative day-to-day changes.
- **Technical indicators:** Simple and exponential moving averages (SMA and EMA), relative strength index (RSI), moving average convergence/divergence (MACD), Bollinger Bands, and average true range (ATR) as a volatility proxy.
- **Statistical and volume features:** Rolling means, standard deviations, maxima and minima; autocorrelation; daily volume change; and current volume relative to its rolling average.
- **Calendar features:** Day of the week, month, month end, and trading day versus holiday classifications.
- **Interaction features:** Price relative to a moving average, the `High − Low` range, and return multiplied by volume.

**Knowledge needed:** Lag and return calculations, technical and statistical indicators, calendar variables, and avoidance of lookahead bias. Compute each feature only from information available at the forecast time.

**Resources from the sheet:** None supplied for this step.

## 5. Prepare chronological LSTM sequences

An LSTM expects sequences rather than independent tabular rows. For a next-day forecast using the previous ten days, one example input contains days 1–10 and its target is day 11. With a sequence length of ten, a 1,000-row dataset yields a first window using rows 0–9 with row 10 as its target, followed by rows 1–10 with row 11 as its target. If there are 20 features, the input tensor has shape **`(number_of_samples, 10, 20)`**. The sheet suggests considering window lengths between 10 and 60 observations.

Preserve time order when making train, validation, and test sets; do not use a random split. The sheet gives **70% / 15% / 15%** as one split example and separately mentions **four years for training, four months for validation, and eight months for testing** as another example. Keep later observations out of model fitting. Construct sliding windows so each target immediately follows its input window and no training target falls into the validation or test period.

The sheet includes this sliding-window function (its original Python is unchanged):

```python
def create_sequences(X, y, time_steps=10):
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        Xs.append(X[i:i+time_steps])
        ys.append(y[i+time_steps])
    return np.array(Xs), np.array(ys)
```

The sheet also illustrates the 70/15/15 split with `train_size = int(len(df) * 0.7)`, `val_size = int(len(df) * 0.15)`, and slices of `X` and `y` at those boundaries. Treat these as illustrative fragments: `X`, `y`, and `np` must be defined before running them, and the order of splitting and creating windows must be implemented consistently. Fit any learned preprocessing, including scaling, on the training portion only.

**Knowledge needed:** Sliding windows, NumPy and pandas sequence creation, chronological splits, and the three-dimensional LSTM input format.

**Resources from the sheet:** [1](https://www.youtube.com/watch?v=i4vGKgbtf1U)

## 6. Train the LSTM

Feed the prepared input sequences and targets into an LSTM to learn temporal patterns. The sheet describes an architecture with dropout to reduce overfitting and a dense output layer to predict the future price. Choose a suitable loss function, such as mean squared error (MSE), and an optimizer, such as Adam. Train on the training data and monitor performance on the validation data at the end of each epoch to select a model. Consider early stopping while tuning the architecture and hyperparameters.

**Knowledge needed:** LSTM layers and hyperparameters; dropout and early stopping; loss functions such as MSE and MAE; Adam; Python, TensorFlow/Keras, training, validation, and evaluation.

**Resources from the sheet:** [1](https://medium.com/@aditib259/predicting-stock-prices-using-lstms-time-series-forecasting-a-step-by-step-guide-a70ebb04bbb8) · [2](https://www.youtube.com/watch%3Fv%3DVbj2Zzwg8jc&q=EgQzDxjiGPTNrckGIjAwCYo4p0KNJAkfolGUGf0bCr1zTpfMUJ-B7A3z6vRscySIUWNU2j65LOANvq8keeYyAnJSWgFD) (URL reproduced exactly as stored in the sheet)

## 7. Validate and evaluate

Use validation data to tune hyperparameters and monitor overfitting. Use the held-out test data for the final evaluation on unseen observations. The sheet lists:

- **MSE:** Mean squared error.
- **RMSE:** Root mean squared error, expressed in the target variable's units.
- **MAE:** Mean absolute error.
- **MAPE:** Mean absolute percentage error.

**Knowledge needed:** Calculating and interpreting MSE, RMSE, MAE, and MAPE.

**Resources from the sheet:** [1](https://codesignal.com/learn/courses/time-series-forecasting-with-lstms/lessons/evaluating-and-visualizing-lstm-model-performance) · [2](https://medium.com/@ottaviocalzone/mae-mse-rmse-and-f1-score-in-time-series-forecasting-d04021ffa7ce) · [3](https://www.youtube.com/watch?v=cFj4KypOrMk)

## 8. Optional: Study Dockerization

If time remains, study a brief introduction to packaging the project with Docker.

**Resource from the sheet:** [1](https://blog.faradars.org/%D8%A2%D9%85%D9%88%D8%B2%D8%B4-%D8%AF%D8%A7%DA%A9%D8%B1-docker-%D8%B1%D8%A7%DB%8C%DA%AF%D8%A7%D9%86/)

## Expected deliverables, in the sheet's priority order

1. A selected market and asset, plus **three to five years of raw data** in a `.csv` file.
2. A **cleaned CSV** with missing values handled, dates corrected, and unrealistic price jumps removed.
3. A **feature-engineered CSV** containing lags, technical indicators, statistical features, and calendar features.
4. **LSTM input sequences** after chronological division into training, validation, and test sets.
5. A **saved `.h5` model in Google Colab**, together with training loss and validation loss plots.
6. **Test-set evaluation** with MAE, RMSE, and MAPE.
7. A **document** summarizing the steps, parameters, and techniques used.

## Mentoring and progress fields in the source

The task sheet provides columns to record (a) whether a mentee should meet the mentor before or after each deliverable, (b) progress toward each deliverable and what was learned, and (c) actions needed before the next meeting. **No entries are supplied in those columns.** The sheet also leaves deliverable rows 8–10 blank.

## Source clarifications

- The skills column labels steps 6–8 as **7–9**, although the actual task steps are numbered **6–8**. The sections here follow the task-step numbers.
- The sheet's claim that collecting three to five years of data avoids overfitting is a motivation, not a guarantee; sample count and model performance still need validation.
- Its two example split schemes are alternatives, not equivalent proportions. Its sequence and split code fragments need to be assembled carefully to prevent information leakage.
- The second training resource has an unusual encoded URL in the source. The link is preserved without guessing a replacement.
