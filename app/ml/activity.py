"""Activity log: who did what, and when. Shown to IT admins on the Admin page."""
import math
import sqlite3
from datetime import datetime, timedelta

from app.ml.database import get_db


def _ensure_table(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            logged_at  TEXT NOT NULL,
            user_email TEXT,
            user_name  TEXT,
            role       TEXT,
            action     TEXT NOT NULL,
            details    TEXT,
            ip_address TEXT
        )
    ''')


def log_activity(action, details='', user_email=None, user_name=None, role=None, ip_address=None):
    """Record one action. A logging problem must never stop the action itself."""
    try:
        conn = get_db()
        _ensure_table(conn)
        conn.execute(
            'INSERT INTO activity_log (logged_at, user_email, user_name, role, action, details, ip_address) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             user_email, user_name, role, action, details, ip_address)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass


def get_recent_activity(limit=50):
    conn = get_db()
    _ensure_table(conn)
    rows = conn.execute('SELECT * FROM activity_log ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]




# ── Sign-in attempt limit ──
MAX_FAILED_LOGINS = 5    # failed attempts allowed per account...
FAILED_WINDOW_MIN = 15   # ...within this many minutes,
LOCK_MINUTES      = 5    # after which sign-in is paused for this long
_TIME_FMT = '%Y-%m-%d %H:%M:%S'


def _ensure_attempts_table(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            email        TEXT NOT NULL,
            ip_address   TEXT,
            attempted_at TEXT NOT NULL
        )
    ''')


def _norm(email):
    return (email or '').strip().lower()


def _recent_failures(conn, email):
    cutoff = (datetime.now() - timedelta(minutes=FAILED_WINDOW_MIN)).strftime(_TIME_FMT)
    return conn.execute(
        'SELECT attempted_at FROM login_attempts WHERE email = ? AND attempted_at >= ? '
        'ORDER BY attempted_at DESC', (_norm(email), cutoff)).fetchall()


def record_failed_login(email, ip_address=None):
    try:
        conn = get_db()
        _ensure_attempts_table(conn)
        conn.execute('INSERT INTO login_attempts (email, ip_address, attempted_at) VALUES (?, ?, ?)',
                     (_norm(email), ip_address, datetime.now().strftime(_TIME_FMT)))
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass


def clear_failed_logins(email):
    try:
        conn = get_db()
        _ensure_attempts_table(conn)
        conn.execute('DELETE FROM login_attempts WHERE email = ?', (_norm(email),))
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass


def failed_logins_left(email):
    """How many more failed attempts this account has before sign-in is paused."""
    try:
        conn = get_db()
        _ensure_attempts_table(conn)
        count = len(_recent_failures(conn, email))
        conn.close()
    except sqlite3.Error:
        return MAX_FAILED_LOGINS
    return max(0, MAX_FAILED_LOGINS - count)


def login_lock_minutes(email):
    """Minutes left before this account may try to sign in again (0 = not locked)."""
    try:
        conn = get_db()
        _ensure_attempts_table(conn)
        rows = _recent_failures(conn, email)
        conn.close()
    except sqlite3.Error:
        return 0
    if len(rows) < MAX_FAILED_LOGINS:
        return 0
    last = datetime.strptime(rows[0]['attempted_at'], _TIME_FMT)
    seconds = (last + timedelta(minutes=LOCK_MINUTES) - datetime.now()).total_seconds()
    return max(0, math.ceil(seconds / 60))