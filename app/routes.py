from flask import Blueprint, render_template, request, redirect, url_for, session
from app.ml.predict import run_forecast
from app.ml.storage import save_forecast, get_latest_forecast, get_all_forecasts, delete_forecast_by_id
from app.ml.auth import verify_password
from functools import wraps

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
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        user = verify_password(email, password)
        if user:
            session['user_email'] = user['email']
            session['user_name']  = user['name']
            session['user_role']  = user['role']
            return redirect(url_for('main.dashboard'))
        else:
            error = 'Invalid email or password. Please try again.'
    return render_template('login.html', error=error)

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
    forecast = session.get('last_forecast', None)
    return render_template('forecast_result.html', forecast=forecast)

@main.route('/history')
@login_required
def history():
    rows = get_all_forecasts()
    return render_template('history.html', rows=rows)

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