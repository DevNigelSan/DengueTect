from flask import Blueprint, render_template, request, redirect, url_for

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        # TODO: add real auth logic
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@main.route('/input', methods=['GET', 'POST'])
def climate_input():
    if request.method == 'POST':
        # TODO: pass form data to ML model
        return redirect(url_for('main.forecast_result'))
    return render_template('climate_input.html')

@main.route('/result')
def forecast_result():
    # TODO: receive model output and pass to template
    return render_template('forecast_result.html')