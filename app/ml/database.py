import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / 'data' / 'denguesense.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            email    TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL DEFAULT 'health_officer'
        )
    ''')

    # Forecasts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            barangay        TEXT NOT NULL,
            week_date       TEXT NOT NULL,
            predicted_cases INTEGER NOT NULL,
            outbreak_proba  REAL NOT NULL,
            risk_level      TEXT NOT NULL,
            rain_w1         REAL, rain_w2 REAL, rain_w3 REAL, rain_w4 REAL,
            temp_w1         REAL, temp_w2 REAL, temp_w3 REAL, temp_w4 REAL,
            humid_w1        REAL, humid_w2 REAL, humid_w3 REAL, humid_w4 REAL,
            cases_w1        REAL, cases_w2 REAL, cases_w3 REAL, cases_w4 REAL,
            generated_at    TEXT NOT NULL,
            generated_by    TEXT
        )
    ''')

        # Add newer columns to databases created before they existed
    cursor.execute('PRAGMA table_info(forecasts)')
    existing = [row['name'] for row in cursor.fetchall()]
    new_columns = {
        'xgb_predicted_cases': 'INTEGER',
        'ensemble_cases':      'INTEGER',
        'published':           'INTEGER NOT NULL DEFAULT 0',
        'actual_cases':        'INTEGER',
        'actual_recorded_at':  'TEXT',
        'actual_recorded_by':  'TEXT',
    }
    for name, col_type in new_columns.items():
        if name not in existing:
            cursor.execute(f'ALTER TABLE forecasts ADD COLUMN {name} {col_type}')

    conn.commit()
    conn.close()