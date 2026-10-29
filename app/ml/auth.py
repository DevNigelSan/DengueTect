from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.ml.database import get_db

def init_default_users():
    conn = get_db()
    cursor = conn.cursor()

    defaults = [
        {
            'name':     'Maria Santos',
            'email':    'm.santos@marikina.gov.ph',
            'password': generate_password_hash('health2024'),
            'role':     'health_officer'
        },
        {
            'name':     'Juan dela Cruz',
            'email':    'j.delacruz@marikina.gov.ph',
            'password': generate_password_hash('health2024'),
            'role':     'health_officer'
        },
        {
            'name':     'IT Admin',
            'email':    'admin@marikina.gov.ph',
            'password': generate_password_hash('admin2024'),
            'role':     'admin'
        }
    ]

        # Only fill an empty database, so accounts the admin edits are never re-created
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    for user in defaults:
        cursor.execute(
            'SELECT id FROM users WHERE email = ?', (user['email'],)
        )
        if not cursor.fetchone():
            cursor.execute(
                'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                (user['name'], user['email'], user['password'], user['role'])
            )

    conn.commit()
    conn.close()

def verify_password(email, password):
    """Returns the user if the email and password match (active or not), else None."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', ((email or '').strip().lower(),))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return None
    if check_password_hash(user['password'], password or ''):
        return dict(user)
    return None

# ── Account management (Admin page) ──
ROLES = {'health_officer': 'Health Officer', 'admin': 'IT Admin'}
MIN_PASSWORD = 8

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, role, active, created_at FROM users '
                   'ORDER BY active DESC, role, name')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def get_user(user_id):
    conn = get_db()
    row = conn.execute('SELECT id, name, email, role, active FROM users WHERE id = ?',
                       (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def is_active_user(email):
    """False if the account was deactivated or deleted (used to end open sessions)."""
    conn = get_db()
    row = conn.execute('SELECT active FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return bool(row) and bool(row['active'])

def _active_admin_count(conn):
    return conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND active = 1").fetchone()[0]

def _check_fields(name, email, role, password, password_required):
    if not name or len(name) < 2:
        return 'Please enter the full name.'
    if not email or '@' not in email or '.' not in email.split('@')[-1] or ' ' in email:
        return 'Please enter a valid email address.'
    if role not in ROLES:
        return 'Please choose a role.'
    if password or password_required:
        if len(password or '') < MIN_PASSWORD:
            return f'The password must be at least {MIN_PASSWORD} characters.'
    return None

def create_user(name, email, role, password):
    """Returns (user_id, None) on success or (None, error message)."""
    name, email = (name or '').strip(), (email or '').strip().lower()
    error = _check_fields(name, email, role, password, password_required=True)
    if error:
        return None, error
    conn = get_db()
    if conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        conn.close()
        return None, 'An account with this email already exists.'
    cur = conn.execute(
        'INSERT INTO users (name, email, password, role, active, created_at) VALUES (?, ?, ?, ?, 1, ?)',
        (name, email, generate_password_hash(password), role, datetime.now().strftime('%Y-%m-%d %H:%M'))
    )
    conn.commit()
    conn.close()
    return cur.lastrowid, None

def update_user(user_id, name, email, role, new_password=''):
    """Edits name, email, role and (optionally) resets the password. Returns an error message or None."""
    name, email = (name or '').strip(), (email or '').strip().lower()
    error = _check_fields(name, email, role, new_password, password_required=False)
    if error:
        return error
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return 'That account no longer exists.'
    if conn.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user_id)).fetchone():
        conn.close()
        return 'Another account already uses this email.'
    if user['role'] == 'admin' and role != 'admin' and user['active'] and _active_admin_count(conn) <= 1:
        conn.close()
        return 'This is the only active IT Admin, so its role cannot be changed.'
    conn.execute('UPDATE users SET name = ?, email = ?, role = ? WHERE id = ?', (name, email, role, user_id))
    if new_password:
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(new_password), user_id))
    conn.commit()
    conn.close()
    return None

def set_user_active(user_id, active, current_email):
    """Activates or deactivates an account. Returns an error message or None."""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return 'That account no longer exists.'
    if not active:
        if user['email'] == current_email:
            conn.close()
            return 'You cannot deactivate the account you are signed in with.'
        if user['role'] == 'admin' and _active_admin_count(conn) <= 1:
            conn.close()
            return 'This is the only active IT Admin, so it cannot be deactivated.'
    conn.execute('UPDATE users SET active = ? WHERE id = ?', (1 if active else 0, user_id))
    conn.commit()
    conn.close()
    return None