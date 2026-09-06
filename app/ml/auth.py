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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return None
    if check_password_hash(user['password'], password):
        return dict(user)
    return None

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, role FROM users ORDER BY id')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users