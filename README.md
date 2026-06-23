# DengueTect
Dengue Outbreak Forecasting System for flood-prone barangays along the Marikina River.

## Overview
DengueTect is a machine learning-powered web application that forecasts dengue outbreaks
2–4 weeks in advance for Barangays Nangka, Tumana, and Malanday in Marikina City.

## Features
- Random Forest model for weekly case count prediction
- Logistic Regression model for outbreak probability classification
- Tiered alert system: Low / Moderate / High risk
- Climate input dashboard: rainfall, temperature, humidity (4-week lag)
- Barangay-level switching for targeted monitoring

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

## Status
- [x] Project structure
- [x] Login page
- [x] Forecast dashboard
- [ ] ML model integration
- [ ] Climate data pipeline
- [ ] User authentication