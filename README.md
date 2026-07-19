# DengueTect
Dengue Outbreak Forecasting System for flood-prone barangays along the Marikina River.

## Overview
DengueTect is a machine learning-powered web application that forecasts dengue outbreaks
2–4 weeks in advance for Barangays Nangka, Tumana, and Malanday in Marikina City.

## Features
- Random Forest model for weekly case count prediction
- Logistic Regression model for outbreak probability classification
- Tiered alert system: Low / Moderate / High risk
- Climate input form with 4-week lag variable entry
- Barangay-level switching for targeted monitoring
- Forecast history log with filtering by barangay and risk level
- Printable forecast result reports
- Admin panel for user management and model configuration

## Tech Stack
- Python 3.14 / Flask 3.x
- Scikit-learn, Pandas, NumPy
- Jinja2 templates, vanilla JS
- PAGASA + Open-Meteo climate data

## Setup
```bash
pip install -r requirements.txt
python run.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Pages
- `/` → redirects to login
- `/login` → login page
- `/dashboard` → forecast dashboard
- `/input` → climate data input form
- `/result` → forecast result report
- `/history` → forecast history log
- `/admin` → admin panel

## Default Accounts

| Role | Email | Password |
|------|-------|----------|
| Health Officer | m.santos@marikina.gov.ph | health2024 |
| IT Admin | admin@marikina.gov.ph | admin2024 |

## Status
- [x] Project structure
- [x] Login page
- [x] Forecast dashboard
- [x] Climate input form
- [x] Forecast result report
- [x] Forecast history page
- [x] Admin panel
- [x] 404 error page
- [ ] ML model integration
- [ ] Climate data pipeline
- [ ] User authentication