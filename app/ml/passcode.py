"""Office passcode for publishing forecasts to the public Community page.

The passcode is written on paper and kept in the health office. Only a salted hash is stored here,
so it can't be read back from the database, the code or GitHub.
"""
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from app.ml.database import get_db

MIN_LENGTH = 6
MAX_LENGTH = 20
MAX_TRIES = 5        # wrong tries allowed ...
WINDOW_MINUTES = 15  # ... within this many minutes
LOCK_MINUTES = 5     # before publishing pauses for this long


def _conn():
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS passcode_failures (email TEXT, failed_at TEXT NOT NULL)')
    return conn


def _get(conn, key):
    row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    return row['value'] if row else None


def passcode_status():
    """For the Admin page: whether a passcode is set, and when and by whom it was last changed."""
    conn = _conn()
    status = {'is_set': bool(_get(conn, 'publish_passcode_hash')),
              'changed_at': _get(conn, 'publish_passcode_changed_at'),
              'changed_by': _get(conn, 'publish_passcode_changed_by')}
    conn.close()
    return status


def _recent_failures(conn, email):
    since = (datetime.now() - timedelta(minutes=WINDOW_MINUTES)).isoformat(timespec='seconds')
    rows = conn.execute('SELECT failed_at FROM passcode_failures WHERE email = ? AND failed_at >= ? '
                        'ORDER BY failed_at', (email, since)).fetchall()
    return [datetime.fromisoformat(r['failed_at']) for r in rows]


def lock_minutes(email):
    """Minutes left before this user may try the passcode again (0 if not paused)."""
    conn = _conn()
    fails = _recent_failures(conn, email)
    conn.close()
    if len(fails) < MAX_TRIES:
        return 0
    left = fails[-1] + timedelta(minutes=LOCK_MINUTES) - datetime.now()
    return max(0, int(left.total_seconds() // 60) + 1) if left.total_seconds() > 0 else 0


def _record_failure(conn, email):
    conn.execute('INSERT INTO passcode_failures (email, failed_at) VALUES (?, ?)',
                 (email, datetime.now().isoformat(timespec='seconds')))
    conn.commit()
    return max(0, MAX_TRIES - len(_recent_failures(conn, email)))


def check_passcode(email, code):
    """Returns (ok, reason, number). reason: 'unset', 'locked' (number = minutes left),
    'wrong' (number = tries left) or 'empty'."""
    conn = _conn()
    stored = _get(conn, 'publish_passcode_hash')
    if not stored:
        conn.close()
        return False, 'unset', 0
    conn.close()
    minutes = lock_minutes(email)
    if minutes:
        return False, 'locked', minutes
    code = (code or '').strip()
    if not code:
        return False, 'empty', 0
    conn = _conn()
    if check_password_hash(stored, code):
        conn.execute('DELETE FROM passcode_failures WHERE email = ?', (email,))
        conn.commit()
        conn.close()
        return True, '', 0
    left = _record_failure(conn, email)
    conn.close()
    return False, ('locked' if left == 0 else 'wrong'), (LOCK_MINUTES if left == 0 else left)


def set_passcode(email, current, new, confirm, changed_by):
    """Sets or changes the passcode. Changing it needs the current one. Returns an error message or None."""
    new, confirm = (new or '').strip(), (confirm or '').strip()
    conn = _conn()
    stored = _get(conn, 'publish_passcode_hash')
    conn.close()
    if stored:
        ok, reason, n = check_passcode(email, current)
        if not ok:
            if reason == 'locked':
                return f'Too many wrong passcodes. Try again in {n} minute{"s" if n != 1 else ""}.'
            return 'The current passcode is wrong.' if reason == 'wrong' else 'Enter the current passcode.'
    if not MIN_LENGTH <= len(new) <= MAX_LENGTH or ' ' in new:
        return f'The new passcode must be {MIN_LENGTH} to {MAX_LENGTH} characters, with no spaces.'
    if new != confirm:
        return 'The two new passcodes do not match.'
    conn = _conn()
    for key, value in (('publish_passcode_hash', generate_password_hash(new)),
                       ('publish_passcode_changed_at', datetime.now().strftime('%B %d, %Y · %I:%M %p')),
                       ('publish_passcode_changed_by', changed_by)):
        conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()
    return None


def reset_passcode():
    """Removes the passcode (for a lost passcode). Run on the server by the IT Admin; see the README."""
    conn = _conn()
    conn.execute("DELETE FROM settings WHERE key LIKE 'publish_passcode_%'")
    conn.execute('DELETE FROM passcode_failures')
    conn.commit()
    conn.close()
