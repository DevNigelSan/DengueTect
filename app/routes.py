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