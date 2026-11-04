# DengueTect

**Dengue outbreak forecasting for flood-prone barangays along the Marikina River**

DengueTect is a Flask web application that gives the Marikina City Health Office (CHO) a **one-week-ahead** dengue forecast for **Barangays Nangka, Tumana and Malanday**. Health officers enter the past four weeks of climate and case data. The system then predicts next week's case count, estimates the probability of an outbreak, and assigns a Low / Moderate / High risk level. A public Community page shares reviewed forecasts with residents.

> Thesis project · Group 10 · BSCS-4A · Eulogio "Amang" Rodriguez Institute of Science and Technology (EARIST)

**Live demo:** https://devnigelsan.pythonanywhere.com

---

## Features

### For health officers
- **Outbreak Dashboard**: the latest forecast for each barangay, a status bar for the highest-risk barangay, Community Alerts publishing, quick stats, and a risk map.
- **Climate Input**: choose a barangay and a week, and the past 4 weeks of rainfall, temperature and humidity are fetched automatically from Open-Meteo. For weeks covered by the CHO records (2022 to March 2026), the 4 case boxes fill in automatically. Every value is also checked on the server: impossible values (e.g. negative rainfall, humidity over 100%) are rejected with a clear message, and the other entries are kept. Unusually high case counts trigger a warning at 7 or more and require confirmation at 9 or more. A notice appears when the chosen week is in the past or future.
- **Forecast Report**: projected cases (Random Forest, XGBoost and an ensemble), outbreak probability, risk level, recommended actions, **Forecast Insights** (how this week's climate and cases compare with the same weeks in past years), and a print-ready layout.
- **Actual Outcome (feedback loop)**: once a forecast week has passed, officers record the actual case count on the report. The system shows how close the forecast was, and Model Evaluation tracks live accuracy over time.
- **Forecast History**: every forecast, filterable by barangay and risk level, with **CSV export**, print, delete, and a **Publish** toggle that controls what residents see. Each barangay's current Dashboard forecast is marked and listed first; older and replaced forecasts are labelled.
- **Heatmap**: weekly case intensity per barangay, a week-by-week risk map, and yearly totals. Synthetic and recorded data are clearly separated.
- **Model Evaluation**: plain-language accuracy figures for each barangay, measured on weeks the models never saw.
- **Help Center** (`/faq`): searchable answers, a glossary, and a floating Help button on every staff page.
- **Dark mode**: an optional dark theme, switched with the moon/sun button in the navbar and remembered on each device. Printed reports always use the light design.

### For IT admins
- Everything above, plus:
- **Technical** page: held-out test results for every model and simple baselines, per-barangay metrics, confusion matrices, feature importance ("What Drives the Forecast"), hyperparameters, and the feature set.
- **Admin** panel: live system stats; user accounts (add, edit, reset password, activate and deactivate, with safeguards so the last IT Admin can't be removed); the models currently loaded; and a full **Activity Log** of every action by every user, filterable by role and action, with **Undo** for forecasts, deletions and publishing.

### For residents (no login)
- **Community** page: the latest **published** forecast for each barangay, prevention tips, dengue warning signs, and a resident help panel. A forecast appears here only after a health officer publishes it.

### Security
- Passwords are stored as hashes.
- After 5 failed sign-ins within 15 minutes, sign-in for that account is paused for 5 minutes.
- Every form is protected against cross-site request forgery (CSRF).
- Deactivated accounts are signed out and can't sign in.
- The session secret key is generated on first run and kept out of the code.
- Friendly error pages (400, 404, 405, 500).

---

## How the forecast works

| Step | Detail |
|---|---|
| Inputs | Weekly rainfall, mean temperature and mean humidity for each of the 4 weeks before the forecast week (lags 1–4), the 4-week rolling average of cases, the calendar month, and the barangay: **15 features** in total |
| Case count | **Random Forest** and **XGBoost** regressors, combined as an ensemble (**0.6 × RF + 0.4 × XGBoost**) |
| Outbreak probability | **Blend**: 50% **Logistic Regression** + 50% the chance of reaching the outbreak line given the ensemble's forecast (Poisson). Chosen over Logistic Regression alone on 2024 validation data |
| Outbreak week | **2 or more cases** in a week: the 75th percentile of recorded barangay-weeks before the test period |
| Risk level | **High** at 75% probability or above · **Moderate** at 50–74% · **Low** below 50% |
| Horizon | **1 week ahead** |

### Model performance
Models are trained on **2017–2024** (1,230 weeks: 768 synthetic + 462 recorded) and tested on **recorded weeks from 2025-01-06 to 2026-03-09** (186 weeks, 62 per barangay) that the models never saw during training. No shuffling: the test period comes strictly after the training period.

**Case count** (lower error is better):

| Model | Avg. error (MAE) | RMSE | Within ±1 case | Within ±2 cases |
|---|---|---|---|---|
| Random Forest | ±1.16 | 1.59 | 71.0% | 89.2% |
| XGBoost | ±1.23 | 1.71 | 71.0% | 88.2% |
| **Ensemble** | **±1.17** | **1.61** | **72.0%** | **89.8%** |
| Baseline: same as last week | ±1.38 | 1.92 | 61.3% | 81.7% |
| Baseline: 4-week average | ±1.25 | 1.66 | 64.5% | 88.2% |

**89.8% of test-week forecasts were within 2 cases of the actual count.**

**Outbreak detection:**

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| **LR + Ensemble blend** | **71.0%** | **75.4%** | **51.8%** | **61.4%** |
| Logistic Regression alone | 69.9% | 77.6% | 45.8% | 57.6% |
| Baseline: outbreak if last week was one | 65.6% | 61.2% | 62.7% | 61.9% |

**What drives the forecast** (feature importance on the test weeks): recent cases 52.6%, humidity 21.3%, temperature 15.2%, month 5.8%, rainfall 3.6%, barangay 1.5%. Scrambling all climate inputs together makes forecasts **9.6% less accurate**.

Weekly counts per barangay are small (mostly 0–3), so part of each week's count is random. Even a model that knew the true weekly risk exactly would reach only about 94% within ±2 cases and about 75% on outbreak yes/no.

Per-barangay figures are on the Model Evaluation and Technical pages and in `data/evaluation.json` and `data/evaluation_summary.json`. These numbers change whenever the models are retrained.

---

## Data

| Period | Source | Notes |
|---|---|---|
| **2022–2026** | Recorded weekly dengue cases for the three barangays (Marikina CHO) | Actual case records, up to March 2026 |
| **2017–2021** | **Synthetic** | Generated to give the models more seasonal history (see below) |
| **Climate** | [Open-Meteo Historical Weather API](https://open-meteo.com/) | Daily data aggregated to weekly values for Marikina, lagged 4 weeks |

**About the synthetic data.** The Marikina CHO has confirmed in writing that barangay-level records before 2022 do not exist. To extend the training history, weekly counts for 2017–2021 were generated from **DOH city-wide yearly dengue totals for Marikina**. Each barangay receives its share of the city total (its share of all Marikina cases in 2022–2026), spread across the year using the week-of-year seasonal pattern seen in the recorded data, with Poisson sampling (seed 42). Climate for those years uses the same 4-week lag as the recorded data. Synthetic weeks are used **for training only**, are never part of the test, and are labelled as synthetic everywhere they appear in the app.

---

## Tech stack
- **Backend:** Python 3.13+, Flask 3.x (Blueprint), SQLite, Waitress (network/production server)
- **Machine learning:** scikit-learn, XGBoost, pandas, NumPy, SciPy, joblib
- **Frontend:** Jinja2 templates, vanilla JavaScript and CSS, Leaflet (maps), Chart.js
- **Data:** Open-Meteo archive API, Jupyter notebooks for processing and training
- **Hosting:** PythonAnywhere

---

## Project structure
```
denguesense/
├── app/
│   ├── __init__.py          # App factory, secret key, CSRF protection, error pages, database setup
│   ├── routes.py            # All pages and actions
│   ├── ml/
│   │   ├── predict.py       # Loads the models and runs a forecast
│   │   ├── storage.py       # Saving and reading forecasts
│   │   ├── database.py      # SQLite connection and schema migration
│   │   ├── auth.py          # Accounts, password checks, user management
│   │   ├── activity.py      # Activity Log, undo and sign-in lockout
│   │   └── insights.py      # Forecast Insights and recorded-case lookup
│   ├── templates/           # Jinja2 pages
│   └── static/              # css/ (including dark.css) and js/
├── data/
│   ├── denguesense.db                 # Created automatically on first run (not in git)
│   ├── processed_dataset_extended.csv # Weekly counts and climate, 2017–2026 (not in git)
│   ├── evaluation.json                # Week-by-week test predictions (from notebook 03)
│   ├── evaluation_summary.json        # Held-out test metrics (from notebook 03)
│   ├── feature_importance.json        # What Drives the Forecast (from notebook 03)
│   └── heatmap.json                   # Heatmap data (from notebook)
├── models/                  # Trained models (.pkl), including outbreak_config.pkl
├── instance/
│   └── secret_key.txt       # Generated on first run (not in git)
├── notebooks/
│   ├── 01_data_processing.ipynb
│   ├── 02_model_training.ipynb
│   └── 03_corrected_data_and_evaluation.ipynb   # Current data, training and held-out evaluation
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

- `python run.py` runs on your computer only, and reloads automatically whenever you save a file.
- `python run.py --network` serves the app to phones and computers on the same Wi-Fi through **Waitress**, with debug mode off, and prints the address to open on other devices.
- On a host that sets the `PORT` environment variable, the app runs with Waitress automatically.
- The SQLite database, the secret key and the default accounts are created on the first run.
- The trained models in `models/` are included in the repository. The saved models need the same library versions they were trained with: **scikit-learn 1.9.0** and **XGBoost 3.4.1**. To retrain, run `notebooks/03_corrected_data_and_evaluation.ipynb`.
- `data/processed_dataset_extended.csv` is not in the repository. Without it, the app still runs, but Climate Input can't auto-fill recorded cases and Forecast Insights has no history to compare with.

### Default accounts

| Role | Email | Password |
|---|---|---|
| Health Officer | m.santos@marikina.gov.ph | health2024 |
| Health Officer | j.delacruz@marikina.gov.ph | health2024 |
| IT Admin | admin@marikina.gov.ph | admin2024 |

> **Change these passwords right after the first sign-in** (Admin → Edit), especially on any copy that others can reach. The defaults are public in this repository.

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
| `/admin` | Admin panel and Activity Log | IT Admin |
| `/logout` | Sign out | Staff |

---

## Known limitations
- Forecasts cover **one week ahead** only.
- **2017–2021 training data is synthetic.** It reflects city-wide yearly totals and a typical seasonal pattern, not actual barangay-level cases.
- Coverage is limited to **Nangka, Tumana and Malanday**.
- Climate data comes from a single Marikina grid point and is applied to all three barangays.
- Weekly counts are small, so outbreak yes/no accuracy has a natural ceiling of about 75%.
- Cases are recorded by home address; some are infected elsewhere (work, school, travel), which local climate can't explain.
- Map boundaries for the barangays are approximate.

## Future work
- Add satellite vegetation (NDVI) per barangay to capture local mosquito habitat, since climate data is the same for all three barangays.
- Separate locally acquired from imported cases using travel history, where case records include it.
- Retrain with new CHO records as they become available.