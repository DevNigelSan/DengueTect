import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# Paths to saved models
BASE_DIR   = Path(__file__).resolve().parent.parent.parent
MODEL_DIR  = BASE_DIR / 'models'

# Load models once at startup
rf_model      = joblib.load(MODEL_DIR / 'rf_model.pkl')
lr_model      = joblib.load(MODEL_DIR / 'lr_model.pkl')
label_encoder = joblib.load(MODEL_DIR / 'label_encoder.pkl')
feature_cols  = joblib.load(MODEL_DIR / 'feature_columns.pkl')

def get_risk_level(probability):
    if probability >= 0.75:
        return 'high'
    elif probability >= 0.50:
        return 'moderate'
    else:
        return 'low'

def run_forecast(barangay, week_date, climate_inputs):
    """
    barangay      : str — 'Nangka', 'Tumana', or 'Malanday'
    week_date     : str — 'YYYY-MM-DD'
    climate_inputs: dict with keys:
                    rain_w1..w4, temp_w1..w4, humid_w1..w4
    Returns dict with forecast results.
    """

    # Encode barangay
    brgy_encoded = label_encoder.transform([barangay.capitalize()])[0]

    # Extract climate lag values
    r1 = float(climate_inputs.get('rain_w1', 0))
    r2 = float(climate_inputs.get('rain_w2', 0))
    r3 = float(climate_inputs.get('rain_w3', 0))
    r4 = float(climate_inputs.get('rain_w4', 0))

    t1 = float(climate_inputs.get('temp_w1', 0))
    t2 = float(climate_inputs.get('temp_w2', 0))
    t3 = float(climate_inputs.get('temp_w3', 0))
    t4 = float(climate_inputs.get('temp_w4', 0))

    h1 = float(climate_inputs.get('humid_w1', 0))
    h2 = float(climate_inputs.get('humid_w2', 0))
    h3 = float(climate_inputs.get('humid_w3', 0))
    h4 = float(climate_inputs.get('humid_w4', 0))

    # Rolling mean placeholder (last 4 weeks average)
    cases_roll4 = 0.0

    # Month as seasonal feature
    month = pd.to_datetime(week_date).month

    # Build feature vector matching training columns
    features = pd.DataFrame([{
        'barangay_encoded': brgy_encoded,
        'month':            month,
        'rainfall_lag1':    r1,
        'temp_lag1':        t1,
        'humidity_lag1':    h1,
        'rainfall_lag2':    r2,
        'temp_lag2':        t2,
        'humidity_lag2':    h2,
        'rainfall_lag3':    r3,
        'temp_lag3':        t3,
        'humidity_lag3':    h3,
        'rainfall_lag4':    r4,
        'temp_lag4':        t4,
        'humidity_lag4':    h4,
        'cases_roll4':      cases_roll4,
    }])[feature_cols]

    # Run predictions
    predicted_cases = int(round(max(0, rf_model.predict(features)[0])))
    outbreak_proba  = float(lr_model.predict_proba(features)[0][1])
    risk_level      = get_risk_level(outbreak_proba)

    return {
        'barangay':        barangay.capitalize(),
        'week_date':       week_date,
        'predicted_cases': predicted_cases,
        'outbreak_proba':  round(outbreak_proba * 100, 1),
        'risk_level':      risk_level,
    }