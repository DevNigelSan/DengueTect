from app.ml.database import get_db
from datetime import datetime

def save_forecast(forecast):
    # Stamp the time once so the database and the result page show the same value
    forecast['generated_at'] = forecast.get('generated_at') or datetime.now().strftime('%B %d, %Y · %I:%M %p')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO forecasts (
            barangay, week_date, predicted_cases, xgb_predicted_cases, ensemble_cases, outbreak_proba, risk_level,
            rain_w1, rain_w2, rain_w3, rain_w4,
            temp_w1, temp_w2, temp_w3, temp_w4,
            humid_w1, humid_w2, humid_w3, humid_w4,
            cases_w1, cases_w2, cases_w3, cases_w4,
            generated_at, generated_by
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        forecast.get('barangay'),
        forecast.get('week_date'),
                forecast.get('predicted_cases'),
        forecast.get('xgb_predicted_cases', 0),
        forecast.get('ensemble_cases', 0),
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
        forecast['generated_at'],
        forecast.get('generated_by')
    ))

    conn.commit()
    forecast_id = cursor.lastrowid
    conn.close()
    forecast['id'] = forecast_id
    return forecast_id

def get_latest_forecast(barangay):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM forecasts
        WHERE barangay = ?
        ORDER BY week_date DESC, id DESC LIMIT 1
    ''', (barangay,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_latest_published_forecast(barangay):
    """Newest forecast week that staff have published to the community page."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM forecasts
        WHERE barangay = ? AND published = 1
        ORDER BY week_date DESC, id DESC LIMIT 1
    ''', (barangay,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def toggle_published(forecast_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE forecasts SET published = 1 - published WHERE id = ?',
        (forecast_id,)
    )
    conn.commit()
    conn.close()

def get_all_forecasts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM forecasts ORDER BY id DESC')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_forecast_by_id(forecast_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM forecasts WHERE id = ?', (forecast_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_forecast_by_id(forecast_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM forecasts WHERE id = ?', (forecast_id,))
    conn.commit()
    conn.close()



def set_published(forecast_id, published):
    """Set a forecast as published (1) or hidden from residents (0)."""
    conn = get_db()
    conn.execute('UPDATE forecasts SET published = ? WHERE id = ?', (1 if published else 0, forecast_id))
    conn.commit()
    conn.close()

def restore_forecast(row):
    """Put a deleted forecast back, with its original record number."""
    conn = get_db()
    columns = [c['name'] for c in conn.execute('PRAGMA table_info(forecasts)').fetchall()]
    data = {k: v for k, v in row.items() if k in columns}
    names = ', '.join(data)
    marks = ', '.join('?' for _ in data)
    conn.execute(f'INSERT INTO forecasts ({names}) VALUES ({marks})', tuple(data.values()))
    conn.commit()
    conn.close()    