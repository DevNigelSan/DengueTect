# DengueTect

**Dengue outbreak forecasting for flood-prone barangays along the Marikina River**

DengueTect is a Flask web application that gives the Marikina City Health Office (CHO) a **one-week-ahead** dengue forecast for **Barangays Nangka, Tumana and Malanday**. Health officers enter the past four weeks of climate and case data. The system then predicts next week's case count, estimates the probability of an outbreak, and assigns a Low / Moderate / High risk level. A public Community page shares reviewed forecasts with residents.

> Thesis project · Group 10 · BSCS-4A · Eulogio "Amang" Rodriguez Institute of Science and Technology (EARIST)

---

## Features

### For health officers
- **Outbreak Dashboard**: the latest forecast for each barangay, a status bar for the highest-risk barangay, a recent forecast log, and a map.
- **Climate Input**: choose a barangay and a week, and the past 4 weeks of rainfall, temperature and humidity are fetched automatically from Open-Meteo. You can also enter them by hand. Unusually high case counts trigger a warning at 7 or more and require confirmation at 9 or more.
- **Forecast Report**: projected cases (Random Forest, XGBoost and an ensemble), outbreak probability, risk level, recommended actions, and a print-ready layout.
- **Forecast History**: every forecast, filterable by barangay and risk level, with **CSV export**, print, delete, and a **Publish** toggle that controls what residents see.
- **Heatmap**: weekly case intensity per barangay, a week-by-week risk map, and yearly totals. Synthetic and recorded data are clearly separated.
- **Model Evaluation**: plain-language accuracy figures for each barangay.
- **Help Center** (`/faq`): searchable answers, a glossary, and a floating Help button on every staff page.

### For IT admins
- Everything above, plus the **Technical** page (detailed metrics, confusion matrices, hyperparameters, feature set) and the **Admin** panel (user management).

### For residents (no login)
- **Community** page: the latest **published** forecast for each barangay, prevention tips, dengue warning signs, and a resident help panel. A forecast appears here only after a health officer publishes it from Forecast History.

---

## How the forecast works

| Step | Detail |
|---|---|
| Inputs | Weekly rainfall, mean temperature and mean humidity for each of the 4 weeks before the forecast week (lags 1–4), the 4-week rolling average of cases, the calendar month, and the barangay: **15 features** in total |
| Case count | **Random Forest** and **XGBoost** regressors, combined as an ensemble (**0.6 × RF + 0.4 × XGBoost**) |
| Outbreak probability | **Logistic Regression** classifier |
| Risk level | **High** at 75% probability or above · **Moderate** at 50–74% · **Low** below 50% |
| Horizon | **1 week ahead** |

### Model performance (current models)
Measured on a chronological 80/20 split (no shuffling; the last 20% of weeks are held out):

| Model | Metric |
|---|---|
| Random Forest | RMSE 1.83 · R² 0.42 |
| XGBoost | RMSE 2.05 · R² 0.27 |
| Logistic Regression | Accuracy 88.7% · Precision 82.6% |

Per-barangay figures are on the Model Evaluation and Technical pages and in `data/evaluation.json`. These numbers will change whenever the models are retrained.

---

## Data

| Period | Source | Notes |
|---|---|---|
| **2022–2026** | Recorded weekly dengue cases for the three barangays | Actual case records |
| **2017–2021** | **Synthetic** | Generated to give the models more seasonal history (see below) |
| **Climate** | [Open-Meteo Historical Weather API](https://open-meteo.com/) | Daily data aggregated to weekly values for Marikina |

**About the synthetic data.** The Marikina CHO has confirmed in writing that barangay-level records before 2022 do not exist. To extend the training history, weekly counts for 2017–2021 were generated from **DOH city-wide yearly dengue totals for Marikina**. Each yearly total was divided among the three barangays and spread across the year using the week-of-year seasonal pattern seen in the 2022–2026 data, with Poisson sampling (seed 42). These weeks are used **for training only** and are labelled as synthetic everywhere they appear in the app.

---

## Tech stack
- **Backend:** Python 3.14, Flask 3.x (Blueprint), SQLite
- **Machine learning:** scikit-learn, XGBoost, pandas, NumPy, joblib
- **Frontend:** Jinja2 templates, vanilla JavaScript and CSS, Leaflet (maps), Chart.js
- **Data:** Open-Meteo archive API, Jupyter notebooks for processing and training

---

## Project structure
```
denguesense/
├── app/
│   ├── __init__.py          # App factory, session settings, database setup
│   ├── routes.py            # All pages and actions
│   ├── ml/
│   │   ├── predict.py       # Loads the models and runs a forecast
│   │   ├── storage.py       # Saving and reading forecasts
│   │   ├── database.py      # SQLite connection and schema migration
│   │   └── auth.py          # Default users and password checks
│   ├── templates/           # Jinja2 pages
│   └── static/              # css/ and js/
├── data/
│   ├── denguesense.db       # Created automatically on first run
│   ├── evaluation.json      # Model evaluation results (from notebook)
│   └── heatmap.json         # Heatmap data (from notebook)
├── models/                  # Trained models (.pkl)
├── notebooks/
│   ├── 01_data_processing.ipynb
│   └── 02_model_training.ipynb
├── requirements.txt
├── Procfile
└── run.py
```

---

## Setup

```bash
pip install -r requirements.txt
python run.py
```

Then open **http://127.0.0.1:5000**.

- When run locally, the app reloads automatically whenever you save a file. On a host that sets the `PORT` environment variable, it runs without debug mode.
- The SQLite database and default accounts are created on the first run.
- The app needs these files in `models/`: `rf_model.pkl`, `xgb_model.pkl`, `lr_model.pkl`, `label_encoder.pkl`, `feature_columns.pkl`. If the folder is empty after cloning (`.pkl` files are listed in `.gitignore`), run `notebooks/02_model_training.ipynb` to generate them.

### Default accounts

| Role | Email | Password |
|---|---|---|
| Health Officer | m.santos@marikina.gov.ph | health2024 |
| Health Officer | j.delacruz@marikina.gov.ph | health2024 |
| IT Admin | admin@marikina.gov.ph | admin2024 |

Residents don't need an account. They can open the Community page from the login screen.

---

## Pages

| Route | Page | Access |
|---|---|---|
| `/` | Redirects to login | Public |
| `/login` | Sign in (with Remember me) | Public |
| `/community` | Community dengue alerts | Public |
| `/dashboard` | Outbreak Dashboard | Staff |
| `/input` | Climate Input | Staff |
| `/result` | Latest forecast report (`/result?id=<id>` for a specific one) | Staff |
| `/history` | Forecast History | Staff |
| `/history/export` | Download forecast history as CSV | Staff |
| `/evaluation` | Model Evaluation | Staff |
| `/heatmap` | Heatmap | Staff |
| `/faq` | Help Center | Staff |
| `/technical` | Technical metrics | IT Admin |
| `/admin` | Admin panel | IT Admin |
| `/logout` | Sign out | Staff |

---

## Known limitations
- Forecasts cover **one week ahead** only.
- **2017–2021 training data is synthetic.** It reflects city-wide yearly totals and a typical seasonal pattern, not actual barangay-level cases.
- Coverage is limited to **Nangka, Tumana and Malanday**.
- Climate data comes from a single Marikina grid point and is applied to all three barangays.
- Map boundaries for the barangays are approximate.