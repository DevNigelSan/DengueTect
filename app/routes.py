from flask import Blueprint, render_template, request, redirect, url_for, session
from app.ml.predict import run_forecast
from app.ml.storage import save_forecast, get_latest_forecast, get_all_forecasts, delete_forecast_by_id, get_latest_published_forecast, toggle_published
from datetime import date
from app.ml.auth import verify_password
from functools import wraps
import json
from pathlib import Path

main = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('main.login'))
        if session.get('user_role') != 'admin':
             return redirect(url_for('main.history'))
        return f(*args, **kwargs)
    return decorated

@main.route('/')
def index():
    return redirect(url_for('main.login'))

ROLE_LABELS = {'health_officer': 'Health Officer', 'admin': 'IT Admin'}

@main.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    error_hint = None
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        role     = request.form.get('role', 'health_officer')
        user = verify_password(email, password)
        if not user:
            error = 'Invalid email or password. Please try again.'
            error_hint = 'Check for typos and Caps Lock. Forgot your password? Contact your IT Admin.'
        elif user['role'] != role:
            error = (f"This account is registered as {ROLE_LABELS.get(user['role'], user['role'])}, "
                     f"not {ROLE_LABELS.get(role, role)}.")
            error_hint = 'Select the correct role under "Sign in as" and try again.'
        else:
            session['user_email'] = user['email']
            session['user_name']  = user['name']
            session['user_role']  = user['role']
            session.permanent = request.form.get('remember') == 'on'
            return redirect(url_for('main.dashboard'))
    return render_template('login.html', error=error, error_hint=error_hint,
                           email=request.form.get('email', ''),
                           role=request.form.get('role', 'health_officer'))

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    nangka   = get_latest_forecast('Nangka')
    tumana   = get_latest_forecast('Tumana')
    malanday = get_latest_forecast('Malanday')
    return render_template('dashboard.html',
        nangka=nangka,
        tumana=tumana,
        malanday=malanday,
        active_forecast=nangka or tumana or malanday
    )

@main.route('/input', methods=['GET', 'POST'])
@login_required
def climate_input():
    if request.method == 'POST':
        barangay  = request.form.get('barangay')
        week_date = request.form.get('week_date')

        climate_inputs = {
            'rain_w1':   request.form.get('rain_w1'),
            'rain_w2':   request.form.get('rain_w2'),
            'rain_w3':   request.form.get('rain_w3'),
            'rain_w4':   request.form.get('rain_w4'),
            'temp_w1':   request.form.get('temp_w1'),
            'temp_w2':   request.form.get('temp_w2'),
            'temp_w3':   request.form.get('temp_w3'),
            'temp_w4':   request.form.get('temp_w4'),
            'humid_w1':  request.form.get('humid_w1'),
            'humid_w2':  request.form.get('humid_w2'),
            'humid_w3':  request.form.get('humid_w3'),
            'humid_w4':  request.form.get('humid_w4'),
            'cases_w1':  request.form.get('cases_w1'),
            'cases_w2':  request.form.get('cases_w2'),
            'cases_w3':  request.form.get('cases_w3'),
            'cases_w4':  request.form.get('cases_w4'),
            'generated_by': session.get('user_name'),
        }

        result = run_forecast(barangay, week_date, climate_inputs)
        result.update(climate_inputs)
        save_forecast(result)
        session['last_forecast'] = result
        return redirect(url_for('main.forecast_result'))

    return render_template('climate_input.html')

@main.route('/result')
@login_required
def forecast_result():
    forecast_id = request.args.get('id', type=int)
    if forecast_id:
        from app.ml.storage import get_forecast_by_id
        forecast = get_forecast_by_id(forecast_id)
    else:
        forecast = session.get('last_forecast', None)
    return render_template('forecast_result.html', forecast=forecast)

@main.route('/history')
@login_required
def history():
    rows = get_all_forecasts()
    return render_template('history.html', rows=rows)

@main.route('/faq')
@login_required
def faq():
    return render_template('faq.html')

def _with_age(forecast):
    """Adds how many days old a forecast's week is, for the stale-alert notice."""
    if not forecast:
        return None
    try:
        forecast['age_days'] = (date.today() - date.fromisoformat(forecast['week_date'])).days
    except (ValueError, TypeError):
        forecast['age_days'] = None
    return forecast

@main.route('/community')
def community():
    # Public, view-only page for residents. Shows only forecasts staff have published.
    return render_template('community.html',
        nangka=_with_age(get_latest_published_forecast('Nangka')),
        tumana=_with_age(get_latest_published_forecast('Tumana')),
        malanday=_with_age(get_latest_published_forecast('Malanday'))
    )

@main.route('/toggle-publish', methods=['POST'])
@login_required
def toggle_publish():
    forecast_id = request.form.get('forecast_id')
    if forecast_id:
        toggle_published(int(forecast_id))
    return redirect(url_for('main.history'))

@main.route('/admin')
@admin_required
def admin():
    from app.ml.auth import get_all_users
    users = get_all_users()
    return render_template('admin.html', users=users)

@main.route('/delete-forecast', methods=['POST'])
@login_required
def delete_forecast():
    forecast_id = request.form.get('forecast_id')
    if forecast_id:
        delete_forecast_by_id(int(forecast_id))
    return redirect(url_for('main.dashboard'))

@main.route('/evaluation')
@login_required
def evaluation():
    eval_path = Path(__file__).resolve().parent.parent / 'data' / 'evaluation.json'
    with open(eval_path, 'r') as f:
        eval_data = json.load(f)
    return render_template('evaluation.html', eval_data=eval_data)

@main.route('/heatmap')
@login_required
def heatmap():
    import json
    from pathlib import Path
    heatmap_path = Path(__file__).resolve().parent.parent / 'data' / 'heatmap.json'
    with open(heatmap_path, 'r') as f:
        heatmap_data = json.load(f)
    return render_template('heatmap.html', heatmap_data=heatmap_data)


@main.route('/technical')
@admin_required
def technical():
    import json
    from pathlib import Path
    eval_path = Path(__file__).resolve().parent.parent / 'data' / 'evaluation.json'
    with open(eval_path, 'r') as f:
        eval_data = json.load(f)
    return render_template('technical.html', eval_data=eval_data)