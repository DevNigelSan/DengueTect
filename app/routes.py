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

def _publish_status():
    """Latest forecast per barangay and what residents currently see, for the Community Alerts panel."""
    status = []
    for brgy in ['Nangka', 'Tumana', 'Malanday']:
        latest = get_latest_forecast(brgy)
        shown  = get_latest_published_forecast(brgy)
        if not latest:
            state = 'none'
        elif shown and shown['id'] == latest['id']:
            state = 'live'
        else:
            state = 'pending'
        status.append({'barangay': brgy, 'latest': latest, 'shown': shown, 'state': state})
    return status

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
        active_forecast=nangka or tumana or malanday,
        publish=_publish_status()
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

@main.route('/history/export')
@login_required
def export_history():
    import csv, io
    from flask import Response

    columns = [
        ('id', 'ID'), ('barangay', 'Barangay'), ('week_date', 'Forecast Week'),
        ('predicted_cases', 'Projected Cases (RF)'), ('xgb_predicted_cases', 'Projected Cases (XGBoost)'),
        ('ensemble_cases', 'Ensemble Estimate'), ('outbreak_proba', 'Outbreak Probability (%)'),
        ('risk_level', 'Risk Level'),
        ('rain_w1', 'Rainfall W-1 (mm)'), ('rain_w2', 'Rainfall W-2 (mm)'),
        ('rain_w3', 'Rainfall W-3 (mm)'), ('rain_w4', 'Rainfall W-4 (mm)'),
        ('temp_w1', 'Temp W-1 (°C)'), ('temp_w2', 'Temp W-2 (°C)'),
        ('temp_w3', 'Temp W-3 (°C)'), ('temp_w4', 'Temp W-4 (°C)'),
        ('humid_w1', 'Humidity W-1 (%)'), ('humid_w2', 'Humidity W-2 (%)'),
        ('humid_w3', 'Humidity W-3 (%)'), ('humid_w4', 'Humidity W-4 (%)'),
        ('cases_w1', 'Cases W-1'), ('cases_w2', 'Cases W-2'),
        ('cases_w3', 'Cases W-3'), ('cases_w4', 'Cases W-4'),
        ('generated_at', 'Generated At'), ('generated_by', 'Generated By'),
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([label for _, label in columns])
    for row in get_all_forecasts():
        writer.writerow([row.get(key, '') for key, _ in columns])

    filename = f"denguetect_forecast_history_{date.today().isoformat()}.csv"
    # utf-8-sig lets Excel display the ° and · symbols correctly
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

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
    if request.form.get('next') == 'dashboard':
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.history'))

@main.route('/publish-latest', methods=['POST'])
@login_required
def publish_latest():
    # Publishes the newest forecast of every barangay that isn't on the community page yet
    for brgy in ['Nangka', 'Tumana', 'Malanday']:
        f = get_latest_forecast(brgy)
        if f and not f.get('published'):
            toggle_published(f['id'])
    return redirect(url_for('main.dashboard'))

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
    if request.form.get('next') == 'history':
        return redirect(url_for('main.history'))
    return redirect(url_for('main.dashboard'))

# ── Model Evaluation: separate synthetic and recorded weeks ──
def _synthetic_lookup():
    """Which weeks are synthetic. heatmap.json stores each week's source."""
    path = Path(__file__).resolve().parent.parent / 'data' / 'heatmap.json'
    try:
        with open(path, 'r') as f:
            hm = json.load(f)
        return {(brgy, e['week']): e.get('source') == 'synthetic'
                for brgy, weeks in hm['barangays'].items() for e in weeks}
    except (OSError, ValueError, KeyError):
        return {}

def _mean_abs_error(actual, predicted, mask):
    errs = [abs(a - p) for a, p, m in zip(actual, predicted, mask) if m]
    return round(sum(errs) / len(errs), 2) if errs else None

def _outbreak_scores(actual, predicted, mask):
    pairs = [(a, p) for a, p, m in zip(actual, predicted, mask) if m]
    if not pairs:
        return None, None
    tp = sum(1 for a, p in pairs if a == 1 and p == 1)
    fp = sum(1 for a, p in pairs if a == 0 and p == 1)
    correct = sum(1 for a, p in pairs if a == p)
    accuracy  = round(correct / len(pairs) * 100, 1)
    precision = round(tp / (tp + fp) * 100, 1) if (tp + fp) else None
    return accuracy, precision

def _split_evaluation(eval_data):
    lookup = _synthetic_lookup()
    split = {}
    for brgy, data in eval_data.items():
        weeks  = data.get('weeks', [])
        actual = data.get('actual', [])
        if data.get('source'):
            syn = [s == 'synthetic' for s in data['source']]
        else:
            syn = [lookup.get((brgy, w), int(w[:4]) < 2022) for w in weeks]
        real   = [not s for s in syn]
        # Held-out test weeks: recorded weeks the models never saw during training
        test   = [s == 'test' for s in data['split']] if data.get('split') else real
        part = {
            'first_test': test.index(True) if True in test else len(weeks),
            'n_test':     sum(test),
            'recall':     data.get('recall'),
            'syn':        syn,
            'first_real': real.index(True) if True in real else len(weeks),
            'n_syn':      sum(syn),
            'n_real':     sum(real),
            'syn_years':  sorted({int(w[:4]) for w, s in zip(weeks, syn) if s}),
            'real_years': sorted({int(w[:4]) for w, s in zip(weeks, syn) if not s}),
        }
        for key, series in (('rf', 'predicted'), ('xgb', 'xgb'), ('ens', 'ensemble')):
            values = data.get(series) or []
            part[key + '_real'] = _mean_abs_error(actual, values, test) if values else None
            part[key + '_syn']  = _mean_abs_error(actual, values, syn) if values else None
        # Only possible when the notebook exports week-by-week outbreak labels
        if data.get('clf_actual') and data.get('clf_pred'):
            part['acc_real'], part['prec_real'] = _outbreak_scores(data['clf_actual'], data['clf_pred'], test)
            part['acc_syn'],  part['prec_syn']  = _outbreak_scores(data['clf_actual'], data['clf_pred'], syn)
            part['clf_split'] = True
        else:
            part['clf_split'] = False
        split[brgy] = part
    return split

@main.route('/evaluation')
@login_required
def evaluation():
    eval_path = Path(__file__).resolve().parent.parent / 'data' / 'evaluation.json'
    with open(eval_path, 'r') as f:
        eval_data = json.load(f)
    split = _split_evaluation(eval_data)
    first = next(iter(split.values()), {})
    summary_path = Path(__file__).resolve().parent.parent / 'data' / 'evaluation_summary.json'
    try:
        with open(summary_path, 'r') as f:
            summary = json.load(f)
    except (OSError, ValueError):
        summary = None
    prov = {
        'n_syn':      first.get('n_syn', 0),
        'n_real':     first.get('n_real', 0),
        'syn_years':  first.get('syn_years', []),
        'real_years': first.get('real_years', []),
        'clf_split':  all(p['clf_split'] for p in split.values()) if split else False,
        'has_test':   bool(summary),
        'n_test':     first.get('n_test', 0),
        'test_start': summary['test_start'] if summary else '',
    }
    return render_template('evaluation.html', eval_data=eval_data, split=split, prov=prov, summary=summary)

@main.route('/heatmap')
@login_required
def heatmap():
    import json
    from pathlib import Path
    heatmap_path = Path(__file__).resolve().parent.parent / 'data' / 'heatmap.json'
    with open(heatmap_path, 'r') as f:
        heatmap_data = json.load(f)
    first_brgy = next(iter(heatmap_data['barangays'].values()), [])
    years = sorted({int(entry['week'][:4]) for entry in first_brgy}) or [date.today().year]
    syn_years = sorted({int(e['week'][:4]) for e in first_brgy if e.get('source') == 'synthetic'})
    n_syn = sum(1 for e in first_brgy if e.get('source') == 'synthetic')
    prov = {
        'n_syn': n_syn,
        'n_real': len(first_brgy) - n_syn,
        'syn_years': syn_years,
        'real_years': [y for y in years if y not in syn_years],
        'last_week': first_brgy[-1]['week'] if first_brgy else '',
    }
    return render_template('heatmap.html', heatmap_data=heatmap_data, years=years, prov=prov)


@main.route('/technical')
@admin_required
def technical():
    import json
    from pathlib import Path
    eval_path = Path(__file__).resolve().parent.parent / 'data' / 'evaluation.json'
    with open(eval_path, 'r') as f:
        eval_data = json.load(f)
    summary_path = Path(__file__).resolve().parent.parent / 'data' / 'evaluation_summary.json'    
    try:
        with open(summary_path, 'r') as f:
            summary = json.load(f)
    except (OSError, ValueError):
        summary = None
    return render_template('technical.html', eval_data=eval_data,
                           split=_split_evaluation(eval_data), summary=summary)