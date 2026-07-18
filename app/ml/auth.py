import json
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

USERS_FILE = Path(__file__).resolve().parent.parent.parent / 'data' / 'users.json'

def load_users():
    if not USERS_FILE.exists():
        return []
    with open(USERS_FILE, 'r') as f:
        return json.load(f)['users']

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump({'users': users}, f, indent=2)

def get_user_by_email(email):
    users = load_users()
    for u in users:
        if u['email'] == email:
            return u
    return None

def verify_password(email, password):
    user = get_user_by_email(email)
    if not user:
        return None
    if check_password_hash(user['password'], password):
        return user
    return None

def init_default_users():
    users = load_users()
    updated = False
    defaults = [
        {
            'id': 1,
            'name': 'Maria Santos',
            'email': 'm.santos@marikina.gov.ph',
            'password': generate_password_hash('health2024'),
            'role': 'health_officer'
        },
        {
            'id': 2,
            'name': 'IT Admin',
            'email': 'admin@marikina.gov.ph',
            'password': generate_password_hash('admin2024'),
            'role': 'admin'
        }
    ]
    for default in defaults:
        if not any(u['email'] == default['email'] for u in users):
            users.append(default)
            updated = True
    if updated:
        save_users(users)