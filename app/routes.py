from flask import Blueprint, render_template, request, redirect, url_for, session
from app.ml.predict import run_forecast

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        role     = request.form.get('role')
        # TODO: add real auth logic
        session['role'] = role
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main.route('/dashboard')
def dashboard():
    forecast = session.get('last_forecast', None)
    return render_template('dashboard.html', forecast=forecast)

@main.route('/input', methods=['GET', 'POST'])
def climate_input():
    if request.method == 'POST':
        barangay  = request.form.get('barangay')
        week_date = request.form.get('week_date')

        climate_inputs = {
            'rain_w1':  request.form.get('rain_w1'),
            'rain_w2':  request.form.get('rain_w2'),
            'rain_w3':  request.form.get('rain_w3'),
            'rain_w4':  request.form.get('rain_w4'),
            'temp_w1':  request.form.get('temp_w1'),
            'temp_w2':  request.form.get('temp_w2'),
            'temp_w3':  request.form.get('temp_w3'),
            'temp_w4':  request.form.get('temp_w4'),
            'humid_w1': request.form.get('humid_w1'),
            'humid_w2': request.form.get('humid_w2'),
            'humid_w3': request.form.get('humid_w3'),
            'humid_w4': request.form.get('humid_w4'),
        }

        result = run_forecast(barangay, week_date, climate_inputs)
        session['last_forecast'] = result
        return redirect(url_for('main.forecast_result'))

    return render_template('climate_input.html')

@main.route('/result')
def forecast_result():
    forecast = session.get('last_forecast', None)
    return render_template('forecast_result.html', forecast=forecast)

@main.route('/history')
def history():
    return render_template('history.html')

@main.route('/admin')
def admin():
    return render_template('admin.html')    