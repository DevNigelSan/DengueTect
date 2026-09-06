from app.ml.database import get_db
from datetime import datetime

def save_forecast(forecast):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO forecasts (
            barangay, week_date, predicted_cases, outbreak_proba, risk_level,
            rain_w1, rain_w2, rain_w3, rain_w4,
            temp_w1, temp_w2, temp_w3, temp_w4,
            humid_w1, humid_w2, humid_w3, humid_w4,
            cases_w1, cases_w2, cases_w3, cases_w4,
            generated_at, generated_by
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        forecast.get('barangay'),
        forecast.get('week_date'),
        forecast.get('predicted_cases'),
        forecast.get('outbreak_proba'),
        forecast.get('risk_level'),
        forecast.get('rain_w1'), forecast.get('rain_w2'),
        forecast.get('rain_w3'), forecast.get('rain_w4'),
        forecast.get('temp_w1'), forecast.get('temp_w2'),
        forecast.get('temp_w3'), forecast.get('temp_w4'),
        forecast.get('humid_w1'), forecast.get('humid_w2'),
        forecast.get('humid_w3'), forecast.get('humid_w4'),
        forecast.get('cases_w1'), forecast.get('cases_w2'),
        forecast.get('cases_w3'), forecast.get('cases_w4'),
        datetime.now().strftime('%B %d, %Y · %I:%M %p'),
        forecast.get('generated_by')
    ))

    conn.commit()
    conn.close()

def get_latest_forecast(barangay):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM forecasts
        WHERE barangay = ?
        ORDER BY id DESC LIMIT 1
    ''', (barangay,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_forecasts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM forecasts ORDER BY id DESC')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def delete_forecast_by_id(forecast_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM forecasts WHERE id = ?', (forecast_id,))
    conn.commit()
    conn.close()