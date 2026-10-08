نسخه فعلی ریپو را با همان نسخه‌ای که دفعه قبل بررسی کردیم، یعنی حدود commit **`41973b6fdb` در 27 سپتامبر 2026** مقایسه کردم. تغییر اصلی فقط بهینه‌سازی کد نیست؛ پروژه از یک **Daily LSTM experiment** به یک پروژه‌ی دوشاخه‌ی **Daily + Hourly forecasting** تبدیل شده و از نظر طراحی آزمایش هم چند بهبود مهم داشته است.

## جمع‌بندی خیلی کوتاه

نسخه قبلی:

> 5 سال داده روزانه → Feature Engineering → LSTM → پیش‌بینی قیمت پایانی رسمی جلسه بعد

نسخه جدید:

> نسخه روزانه قبلی را حفظ کرده + یک Pipeline مستقل ساعتی ساخته → داده Intraday واقعی را از معاملات خام تجمیع می‌کند → Gapها را کنترل می‌کند → ویژگی‌های نسبی می‌سازد → به‌جای قیمت مطلق، **Log Return** را پیش‌بینی می‌کند → قیمت را بازسازی می‌کند → روی A100 آموزش می‌دهد → نتیجه را با Persistence / Ridge / OHLCV-LSTM مقایسه و مستقل verify می‌کند.

از نظر مهندسی ML، نسخه جدید **به‌طور محسوسی بالغ‌تر** است.

---

# 1. بزرگ‌ترین تغییر: Daily → Daily + Hourly

| مورد               | نسخه قبلی                 | نسخه جدید                                   |
| ------------------ | ------------------------- | ------------------------------------------- |
| فرکانس اصلی        | Daily                     | **Hourly + Daily preserved**                |
| داده اصلی          | قیمت روزانه TSETMC        | **معاملات Intraday تجمیع‌شده به Bar ساعتی** |
| تعداد داده خام     | 1,038 روز                 | **4,273 Bar ساعتی**                         |
| تعداد روز معاملاتی | ~1,038                    | 1,025 روز دارای داده ساعتی                  |
| Missing/Unresolved | 1 رکورد quarantine        | **15 روز unresolved**                       |
| Target             | قیمت پایانی رسمی جلسه بعد | **Last Traded Price در Bar بعدی**           |

یعنی پروژه دیگر صرفاً روی یک Observation در هر روز کار نمی‌کند.

مثلاً:

```text
2026-09-30 09:00
2026-09-30 10:00
2026-09-30 11:00
2026-09-30 12:00
```

هر کدام اکنون یک Observation جداگانه‌اند.

---

# 2. Data Acquisition خیلی جدی‌تر شده

قبلاً داده عمدتاً از خروجی‌های Daily مربوط به `pytse-client` وارد می‌شد.

نسخه جدید یک exporter مستقل اضافه کرده:

```text
export_foolad_hourly.py
```

که برای هر روز معاملاتی:

1. Tradeهای واقعی را دریافت می‌کند.
2. آن‌ها را Cache می‌کند.
3. بر اساس ساعت Resample می‌کند.
4. OHLC + Volume تولید می‌کند.
5. Coverage هر روز را ثبت می‌کند.

Aggregation تقریباً:

$$
\text{Trades}
\rightarrow
\text{1H Bars}
$$

با:

- Open
- High
- Low
- Last Price
- Volume
- Returned Trade Count

انجام می‌شود.

---

# 3. یک پیشرفت مهم: Raw Trades واقعاً Verify می‌شوند

نسخه جدید فقط CSV ساعتی را قبول نمی‌کند.

برای **1,025 فایل معاملات خام**، دوباره aggregation را اجرا می‌کند و بررسی می‌کند که:

$$
ReconstructedBar = ExportedBar
$$

باشد.

یعنی موارد زیر دوباره محاسبه می‌شوند:

$$
Open,\ High,\ Low,\ Last,\ Volume,\ TradeCount
$$

و با CSV نهایی مقایسه می‌شوند.

نتیجه فعلی:

> **تمام 4,273 bar موجود از raw trades بازسازی شده و تطبیق داده شده‌اند.**

این از نظر **Data Provenance** پیشرفت مهمی نسبت به نسخه قبل است.

---

# 4. Missing Data دیگر مخفی نمی‌شود

در نسخه Hourly تعداد:

$$
15
$$

روز unresolved وجود دارد.

اما پروژه آن‌ها را:

- interpolation نمی‌کند
- forward-fill نمی‌کند
- bar مصنوعی نمی‌سازد
- حذف خاموش نمی‌کند

بلکه Coverage آن‌ها را نگه می‌دارد.

مثلاً:

```text
downloaded
downloaded
unresolved
downloaded
...
```

این رویکرد درست‌تری برای Financial Time Series است.

---

# 5. مهم‌تر: Sequence دیگر از Gap عبور نمی‌کند

این یکی از بهترین اصلاحات نسخه جدید است.

فرض کن:

```text
Day A
Day B
Day C  ← missing
Day D
Day E
```

مدل نباید تصور کند:

```text
Day B → Day D
```

یک توالی عادی بدون شکست است.

نسخه جدید داده را به **Segment** تقسیم می‌کند.

در خروجی فعلی:

$$
8\ \text{Segments}
$$

ساخته شده.

Sequenceهای LSTM اجازه ندارند از یک Segment به Segment بعدی عبور کنند.

یعنی:

$$
Sequence_t
\not\ni
KnownMissingDate
$$

این اصلاح از نظر جلوگیری از ساخت الگوی زمانی جعلی بسیار مهم است.

---

# 6. Indicatorها هم بعد از Gap Reset می‌شوند

نسخه قبل Rolling Indicatorها را روی سری روزانه محاسبه می‌کرد.

نسخه جدید برای Hourly Data بعد از روزهای unresolved دوباره Indicatorها را Warm-up می‌کند.

مثلاً اگر یک Gap وجود داشته باشد:

```text
Segment 1
────────────
SMA
EMA
RSI
MACD

[missing date]

Segment 2
────────────
SMA warm-up again
EMA warm-up again
RSI warm-up again
...
```

در نتیجه اطلاعات دو طرف یک Gap نامعلوم با هم مخلوط نمی‌شوند.

---

# 7. Target پروژه تغییر بنیادی کرده

نسخه قبلی مستقیم قیمت را Forecast می‌کرد:

$$
\hat{P}_{t+1}
$$

این برای Financial Time Series همیشه ایده‌آل نیست، چون Price Level می‌تواند در طول سال‌ها بسیار تغییر کند.

نسخه جدید از:

```json
"target_mode": "log_return"
```

استفاده می‌کند.

یعنی Target تبدیل شده به:

$$
r_{t+1}
=
\ln\left(
\frac{P_{t+1}}{P_t}
\right)
$$

مدل ابتدا:

$$
\hat{r}_{t+1}
$$

را پیش‌بینی می‌کند.

بعد قیمت بازسازی می‌شود:

$$
\hat{P}_{t+1}
=
P_t e^{\hat{r}_{t+1}}
$$

این تغییر از نظر Time-Series Modeling قابل دفاع‌تر از یادگیری مستقیم Price Level است.

---

# 8. ارتباط بسیار خوبی با Persistence ایجاد شده

یک ویژگی ظریف ولی مهم طراحی جدید این است که اگر مدل بگوید:

$$
\hat{r}_{t+1}=0
$$

آنگاه:

$$
\hat{P}_{t+1}
=
P_t e^0
=
P_t
$$

پس دقیقاً به:

$$
\boxed{\text{Persistence}}
$$

می‌رسیم.

بنابراین LSTM عملاً یاد می‌گیرد:

> «آیا دلیلی دارم از پیش‌بینی ساده‌ی قیمت فعلی منحرف شوم؟»

این formulation از نسخه قبل منطقی‌تر است.

---

# 9. Feature Engineering از Absolute به Relative تغییر کرده

نسخه قبلی Featureهایی مثل:

```text
adj_open
adj_high
adj_low
adj_official_close
SMA
EMA
rolling_max
...
```

را تا حد زیادی در مقیاس قیمت وارد مدل می‌کرد.

نسخه جدید در حالت Hourly بسیاری از آن‌ها را نسبی می‌کند.

مثلاً:

$$
\text{OpenToLast}
=
\frac{Open}{Last}-1
$$

$$
\text{HighToLast}
=
\frac{High}{Last}-1
$$

$$
\text{LowToLast}
=
\frac{Low}{Last}-1
$$

---

## Moving Averageها هم نسبی شده‌اند

به جای اینکه:

$$
SMA_{20}=2500
$$

مستقیماً به مدل داده شود، چیزی شبیه:

$$
\frac{SMA_{20}}{Price_t}-1
$$

استفاده می‌شود.

این باعث می‌شود مدل کمتر به:

> «فولاد در سال 1401 قیمتش 1,500 بوده ولی در سال 1405 مثلاً 3,000 شده»

وابسته شود.

مدل بیشتر **ساختار نسبی بازار** را می‌بیند.

---

# 10. Volume هم بهتر Transform شده

در نسخه Hourly اضافه شده:

$$
\text{LogVolume}
=
\ln(1+Volume)
$$

یعنی:

```text
log_volume
```

که معمولاً برای Distributionهای شدیداً Skewed مثل حجم معاملات مناسب‌تر از Volume خام است.

---

# 11. Featureهای زمانی ساعتی اضافه شده‌اند

نسخه قبلی داشت:

```text
weekday_sin
weekday_cos
jalali_month_sin
jalali_month_cos
```

نسخه جدید علاوه بر آن‌ها:

```text
hour_sin
hour_cos
elapsed_hours_feature
```

را اضافه کرده.

Hour نیز Cyclic Encode شده:

$$
Hour_{\sin}
=
\sin\left(
\frac{2\pi h}{24}
\right)
$$

$$
Hour_{\cos}
=
\cos\left(
\frac{2\pi h}{24}
\right)
$$

که برای Intraday patterns مفیدتر از یک عدد خام مثل:

```text
9
10
11
12
```

است.

---

# 12. تعداد Featureها

نسخه قبلی:

$$
48
$$

Feature داشت.

نسخه Hourly جدید:

$$
\boxed{49}
$$

Feature دارد.

اما تفاوت مهم‌تر **کیفیت Feature Representation** است، نه عدد 48 در برابر 49.

---

# 13. Dataset مؤثر تقریباً چهار برابر شده

نسخه Daily بعد از Feature Engineering:

$$
1004
$$

Feature Row داشت.

نسخه Hourly:

$$
4009
$$

Feature Bar دارد.

تقریباً:

$$
\frac{4009}{1004}
\approx 3.99
$$

یعنی تقریباً **4 برابر Observation قابل استفاده**.

---

# 14. Train / Validation / Test هم تقریباً چهار برابر شده‌اند

### نسخه قبلی

| Split      | Samples |
| ---------- | ------: |
| Train      |     618 |
| Validation |     132 |
| Test       |     134 |

### نسخه جدید

| Split      |   Samples |
| ---------- | --------: |
| Train      | **2,490** |
| Validation |   **533** |
| Test       |   **535** |

تقریباً:

$$
4\times
$$

داده بیشتر برای هر Split وجود دارد.

البته Windowهای Time Series هنوز overlap دارند؛ بنابراین نمی‌توان گفت 2,490 مشاهده کاملاً مستقل داریم.

---

# 15. Sequence Lengthها با داده Hourly سازگار شده‌اند

قبلاً:

$$
10,\ 30,\ 60
$$

جلسه معاملاتی.

الان:

$$
12,\ 24,\ 60
$$

**Observed Bars**.

شش Candidate هنوز وجود دارد:

$$
3\ \text{sequence lengths}
\times
2\ \text{unit sizes}
$$

یعنی:

```text
12 × 32
12 × 64

24 × 32
24 × 64

60 × 32
60 × 64
```

---

# 16. بهترین Architecture هم تغییر کرده

نسخه Daily:

$$
\boxed{60\ \text{sessions} \times 64\ \text{units}}
$$

انتخاب شده بود.

نسخه Hourly:

$$
\boxed{60\ \text{bars} \times 32\ \text{units}}
$$

انتخاب شده.

Validation RMSE:

$$
29.210
$$

بوده است.

نکته جالب اینکه مدل 32-unit از مدل پیچیده‌تر 64-unit کمی بهتر شده.

یعنی باز هم:

> Bigger model ≠ Better model

---

# 17. تنظیم Training کمی تغییر کرده

| Parameter     |     قبلی |         جدید |
| ------------- | -------: | -----------: |
| Units         |  32 / 64 |      32 / 64 |
| Sequence      | 10/30/60 | **12/24/60** |
| Dropout       |      0.2 |          0.2 |
| Learning Rate |    0.001 |        0.001 |
| Epoch max     |      100 |          100 |
| Batch Size    |       32 |       **64** |
| Patience      |       10 |       **12** |
| Seed          |       42 |           42 |

Architecture هنوز ساده و کنترل‌شده باقی مانده:

```text
Input
 ↓
LSTM
 ↓
Dropout
 ↓
Dense(1)
```

که برای مقایسه علمی بهتر از افزایش بی‌دلیل پیچیدگی است.

---

# 18. GPU حالا به‌صورت واقعی enforce می‌شود

Config جدید دارد:

```json
"required_gpu": "A100"
```

و Training قبل از شروع GPU را بررسی می‌کند.

اگر A100 در TensorFlow قابل مشاهده نباشد:

```text
Training stops
```

نسخه Hourly نهایی روی:

> **NVIDIA A100-SXM4 40 GB**

اجرا شده.

نسخه Daily قبلی روی A100 با 80 GB اجرا شده بود.

بنابراین این مورد را نباید «GPU قوی‌تر» دانست؛ بهبود واقعی این است که **محیط اجرای آزمایش explicit و enforce شده است**.

---

# 19. نتیجه مدل‌ها: تغییر بسیار مهم

### نسخه قبلی — Daily

| Model       |       RMSE |
| ----------- | ---------: |
| Persistence | **60.801** |
| Ridge       |    261.746 |
| OHLCV LSTM  |    390.777 |
| Full LSTM   |    467.071 |

Full LSTM نسبت به Persistence:

$$
7.68\times
$$

بدتر بود.

یعنی:

$$
668.2\%
$$

RMSE بیشتر.

---

# 20. نسخه جدید — Hourly

| Model             |        MAE |       RMSE |       MAPE |
| ----------------- | ---------: | ---------: | ---------: |
| Full-feature LSTM |     22.646 |     33.049 |     0.935% |
| Persistence       | **20.322** |     32.793 | **0.832%** |
| Ridge             |     52.373 |     99.132 |     2.149% |
| OHLCV-only LSTM   |     22.452 | **32.143** |     0.923% |

Full LSTM اکنون فقط:

$$
0.78\%
$$

از Persistence در RMSE بدتر است.

نسبت:

$$
\frac{33.049}{32.793}
\approx
1.008
$$

یعنی تقریباً برابر شده‌اند.

---

# 21. این پیشرفت نسبت به Baseline بسیار چشمگیر است

قبلاً:

$$
RMSE_{\text{LSTM}}
=
7.68\times RMSE_{\text{Persistence}}
$$

الان:

$$
RMSE_{\text{LSTM}}
=
1.008\times RMSE_{\text{Persistence}}
$$

از نظر **فاصله با Baseline همان آزمایش**، این بهبود بسیار بزرگی است.

ولی باید یک هشدار جدی گذاشت:

> نمی‌توان گفت RMSE از 467 به 33 کاهش یافته و بنابراین Accuracy مثلاً 93٪ بهتر شده است.

چون Targetها متفاوت‌اند:

### Daily

$$
\text{Next Session Official Close}
$$

### Hourly

$$
\text{Next Observed Hourly Last Price}
$$

پس مقایسه raw RMSE بین این دو آزمایش **سیب با سیب نیست**.

---

# 22. برای اولین بار یک LSTM از Persistence در RMSE جلو زده

این نتیجه جدید مهم است.

OHLCV-only LSTM:

$$
RMSE=32.143
$$

در حالی که Persistence:

$$
RMSE=32.793
$$

بنابراین:

$$
1-
\frac{32.143}{32.793}
\approx
1.98\%
$$

یعنی OHLCV LSTM تقریباً:

$$
\boxed{1.98\%}
$$

RMSE کمتری از Persistence داشته است.

این اولین نشانه در پروژه است که یک Neural Model روی Test Set در یکی از معیارها Baseline ساده را شکست داده.

---

# 23. اما این نتیجه نباید بیش از حد بزرگ شود

OHLCV-LSTM در RMSE بهتر است، ولی:

### MAE

$$
22.452 > 20.322
$$

و MAPE:

$$
0.923\% > 0.832\%
$$

است.

یعنی Persistence هنوز در MAE و MAPE بهتر است.

پس نتیجه صحیح:

> OHLCV LSTM در RMSE کمی بهتر است، ولی به‌طور کلی بر Persistence مسلط نشده است.

---

# 24. Full Feature Engineering باز هم برنده نشده

Full-feature LSTM:

$$
RMSE=33.049
$$

OHLCV-only:

$$
RMSE=32.143
$$

یعنی Feature Engineering گسترده هنوز از OHLCV ساده بهتر نشده.

این الگوی نسخه قبلی هم حفظ شده است.

در واقع:

$$
RMSE_{\text{OHLCV-LSTM}}
<
RMSE_{\text{Full-feature LSTM}}
$$

در Test RMSE.

پس یک نتیجه علمی پروژه تقویت شده:

> تعداد زیاد Technical Indicator الزاماً Predictive Signal ایجاد نمی‌کند.

---

# 25. یک نکته مثبت مهم: بعد از دیدن Test انتخاب مدل عوض نشده

Validation گفته:

$$
60\times32
$$

Full-feature LSTM بهترین Candidate است.

روی Test، OHLCV-LSTM کمی RMSE بهتری داشته.

اما پروژه نگفته:

> پس OHLCV را مدل اصلی اعلام کنیم.

بلکه همان Validation-selected model را مدل اصلی نگه داشته.

این رفتار صحیح است، چون در غیر این صورت:

$$
\text{Test Set}
$$

عملاً تبدیل به Validation Set می‌شد.

---

# 26. Reproducibility هم قوی‌تر شده

نسخه قبلی Model Reload داشت.

نسخه جدید علاوه بر آن:

- `.keras` reload
- `.h5` reload
- Ridge reload
- OHLCV model reload
- scaler verification
- sequence reconstruction
- full metrics reproduction
- Colab verification
- independent local CPU verification
- source hashes
- bundle checksums
- raw trade checksums

دارد.

---

# 27. Cross-environment verification اضافه شده

مدل روی:

```text
TensorFlow 2.20
A100
```

آموزش دیده.

بعد مدل روی CPU و محیط دیگر دوباره تست شده.

برای OHLCV model حداکثر اختلاف:

$$
0.009377\ \text{Rial}
$$

ثبت شده.

و tolerance رسمی:

$$
0.01\ \text{Rial}
$$

است.

این یک ارتقای خوب برای reproducibility واقعی است.

---

# 28. تعداد تست‌ها هم افزایش پیدا کرده

نسخه قبلی:

$$
27
$$

Test پاس‌شده داشت.

نسخه جدید گزارش می‌کند:

$$
30
$$

Test پاس شده‌اند، همراه با یک optional training integration test که skip شده.

همچنین فایل جدید:

```text
tests/test_hourly.py
```

موارد مهمی را تست می‌کند، از جمله:

- Daily adjustment only once per session
- Gap handling
- Sequence gap prevention
- Training-only scaling
- Log-return reconstruction
- Persistence equivalence
- Feature causality
- Hourly/Daily config separation

---

# 29. Causality test بهتر شده

تست جالبی اضافه شده که بخشی از داده‌های آینده را تغییر می‌دهد و بررسی می‌کند Featureهای گذشته تغییر نکنند.

از نظر مفهومی:

$$
\text{FutureData}
\not\rightarrow
\text{PastFeature}
$$

اگر داده آینده سه برابر شود، Feature مربوط به گذشته نباید تغییر کند.

این تست برای جلوگیری از **Look-ahead Leakage** بسیار ارزشمند است.

---

# 30. Daily و Hourly حالا از هم جدا شده‌اند

Config جدید:

```text
configs/hourly.json
```

اضافه شده.

و importer جدید:

```text
import-hourly
```

وجود دارد.

همچنین کد اجازه نمی‌دهد Snapshot Hourly را اشتباهاً با Config روزانه پردازش کنی.

این جداسازی Architecture پروژه را تمیزتر کرده است.

---

# 31. Notebook مستقل Hourly اضافه شده

نسخه قبلی:

```text
marketforecast_colab.ipynb
```

داشت.

الان:

```text
marketforecast_hourly_colab.ipynb
```

نیز اضافه شده.

این Notebook:

```text
verify bundle
→ run tests
→ train
→ verify models
→ package results
```

را انجام می‌دهد.

---

# 32. Output artifactها بسیار کامل‌تر شده‌اند

نسخه جدید نتیجه کامل Hourly را مستقیماً در Repo منتشر کرده:

```text
results/
└── foolad-hourly-a100/
    ├── data/
    │   └── snapshot/
    ├── training-results/
    │   └── hourly-forecast/
    └── provenance/
```

و یک archive قابل حمل نیز دارد:

```text
artifacts/
└── foolad-hourly-a100-results.zip
```

به همراه:

```text
.sha256
```

---

# 33. Provenance ساختاریافته‌تر شده

نسخه جدید حتی نسخه‌ی دقیق Source Code استفاده‌شده هنگام Training را نگه داشته:

```text
provenance/
└── training-source/
```

یعنی اگر در آینده کد `main` تغییر کند، هنوز می‌توان فهمید:

> «مدلی که این metrics را تولید کرده دقیقاً با چه source codeای ساخته شده است؟»

این از لحاظ MLOps / Research Reproducibility ارتقای مهمی است.

---

# 34. یک فایل آموزشی TSA هم اضافه شده

فایل جدید:

```text
notes/Time_Series_Analysis_(TSA).md
```

حدود 1,500 خط محتوای آموزشی دارد.

این مستقیماً Performance مدل را بهتر نمی‌کند، ولی Repo را از صرفاً پروژه اجرایی به ترکیب:

> implementation + experiment + documentation + learning notes

تبدیل کرده است.

---

# 35. مقایسه نهایی

| جنبه                            | نسخه قبلی  | نسخه جدید                |
| ------------------------------- | ---------- | ------------------------ |
| Daily Forecasting               | ✅         | ✅ حفظ شده               |
| Hourly Forecasting              | ❌         | **✅**                   |
| Raw trade retrieval             | ❌         | **✅**                   |
| Raw trade verification          | ❌         | **✅**                   |
| Coverage log                    | محدود      | **✅ explicit**          |
| Missing-date segmentation       | ❌         | **✅**                   |
| Indicator reset after gap       | ❌         | **✅**                   |
| Absolute-price target           | ✅         | Daily only               |
| Log-return target               | ❌         | **✅ Hourly**            |
| Relative features               | محدود      | **✅ گسترده‌تر**         |
| Hour cyclic features            | ❌         | **✅**                   |
| Usable observations             | 1,004      | **4,009**                |
| Train samples                   | 618        | **2,490**                |
| Test samples                    | 134        | **535**                  |
| Training GPU enforcement        | ❌         | **✅ A100**              |
| Model reload verification       | ✅         | ✅                       |
| Local independent verification  | محدود      | **✅**                   |
| Raw/source checksums            | ✅         | **✅ گسترده‌تر**         |
| Tests                           | 27         | **30 passed**            |
| Portable result bundle          | ✅         | **✅ کامل‌تر**           |
| LSTM vs Persistence             | بسیار ضعیف | **تقریباً برابر**        |
| Any NN beating Persistence RMSE | ❌         | **✅ OHLCV-LSTM +1.98%** |

---

# مهم‌ترین بهبود واقعی از نظر Data Science

اگر بخواهم تغییرات را از نظر اهمیت رتبه‌بندی کنم:

1. **تغییر Target از Price Level به Log Return**
2. **استفاده از Featureهای Relative به جای Price Scale خام**
3. **افزایش حدود چهاربرابری تعداد Sampleها با Hourly Data**
4. **عدم عبور Sequenceها و Indicators از Missing Dates**
5. **بازسازی و Verify هر Hourly Bar از Raw Trades**
6. **حفظ Test Set به‌عنوان Test واقعی و عدم انتخاب مدل بر اساس Test**
7. **Cross-environment reproducibility**
8. **بهبود شدید فاصله LSTM با Persistence**

---

## اما هنوز سه محدودیت جدی وجود دارد

اول اینکه Full-feature LSTM هنوز Persistence را شکست نداده:

$$
33.049 > 32.793
$$

بنابراین هنوز نمی‌توان گفت Feature-rich LSTM predictive advantage اثبات کرده است.

دوم، OHLCV-LSTM فقط در **RMSE** حدود 1.98٪ بهتر است؛ در MAE و MAPE همچنان Persistence بهتر است. این evidence مثبت است، ولی ضعیف و نیازمند تکرار روی بازه‌ها و نمادهای دیگر.

سوم، در داده Hourly هنوز **236 bar در ساعت 13:00 یا بعد از آن** وجود دارد که classification دقیق session آن‌ها مستقلاً تأیید نشده. پروژه درست عمل کرده و آن‌ها را مخفیانه حذف نکرده، اما برای یک نسخه Research-grade بعدی بهتر است این موضوع بررسی شود. همچنین 15 روز unresolved هنوز باقی مانده‌اند.

یک نکته مستندی هم وجود دارد: `docs/implementation_status.md` در diff اصلی Hourly به‌روزرسانی نشده و همچنان بیشتر وضعیت آزمایش Daily را منعکس می‌کند؛ در حالی که `docs/hourly_experiment.md` وضعیت جدید را پوشش می‌دهد. یکپارچه کردن این دو، README و لینک‌های Colab می‌تواند ساختار مستندات را تمیزتر کند.

### ارزیابی کلی

نسخه قبلی را می‌شد یک **پروژه خوب Forecasting با تأکید بر reproducibility** دانست.

نسخه فعلی بیشتر شبیه یک **Research-grade time-series experimentation pipeline** شده است:

$$
\boxed{
\text{Raw Trades}
\rightarrow
\text{Verified Hourly Bars}
\rightarrow
\text{Gap-aware Processing}
\rightarrow
\text{Relative Features}
\rightarrow
\text{LogReturn Forecasting}
\rightarrow
\text{Baseline Comparison}
\rightarrow
\text{Independent Verification}
}
$$

و مهم‌ترین پیشرفت عددی هم این نیست که «RMSE از 467 به 33 رسیده»؛ آن مقایسه معتبر نیست. پیشرفت معتبرتر این است که **Full LSTM از 668٪ بدتر از Persistence در آزمایش قبلی، به تنها 0.78٪ بدتر در آزمایش Hourly رسیده و OHLCV-LSTM حتی در RMSE حدود 1.98٪ از Persistence جلو زده است.** این هنوز اثبات برتری LSTM نیست، ولی نسبت به نسخه قبلی نتیجه بسیار امیدوارکننده‌تر و طراحی آزمایش به‌مراتب قوی‌تر شده است.
