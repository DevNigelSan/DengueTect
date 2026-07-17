import json
import os
from pathlib import Path
from datetime import datetime

STORAGE_DIR  = Path(__file__).resolve().parent.parent.parent / 'data'
FORECAST_FILE = STORAGE_DIR / 'forecasts.json'

def load_forecasts():
    if not FORECAST_FILE.exists():
        return {}
    with open(FORECAST_FILE, 'r') as f:
        return json.load(f)

def save_forecast(forecast):
    forecasts = load_forecasts()
    barangay  = forecast['barangay']

    if barangay not in forecasts:
        forecasts[barangay] = []

    # Add timestamp
    forecast['generated_at'] = datetime.now().strftime('%B %d, %Y · %I:%M %p')

    # Prepend to list (newest first)
    forecasts[barangay].insert(0, forecast)

    # Keep only last 20 per barangay
    forecasts[barangay] = forecasts[barangay][:20]

    with open(FORECAST_FILE, 'w') as f:
        json.dump(forecasts, f, indent=2)

def get_latest_forecast(barangay):
    forecasts = load_forecasts()
    entries   = forecasts.get(barangay, [])
    return entries[0] if entries else None

def get_all_forecasts():
    return load_forecasts()