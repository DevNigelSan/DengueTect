"""Plain-language insights for a forecast, comparing it with the historical records."""
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent.parent / 'data' / 'processed_dataset_extended.csv'


@lru_cache(maxsize=1)
def _history():
    d = pd.read_csv(DATA_PATH, parse_dates=['week_start'])
    # rainfall_lag on week W is the weather of week W-4, so shift it back to the week it happened
    clim = d.drop_duplicates('week_start')[['week_start', 'rainfall_lag', 'temp_lag', 'humidity_lag']].copy()
    clim['weather_week'] = clim['week_start'] - pd.Timedelta(weeks=4)
    clim['woy'] = clim['weather_week'].dt.isocalendar().week.astype(int)
    # Case history: recorded (real) weeks only, never the synthetic estimates
    real = d[d['source'] == 'real'].copy()
    real['woy'] = real['week_start'].dt.isocalendar().week.astype(int)
    return clim, real


def _near_week(series, woy, spread=1):
    """Weeks of the year within ±spread of woy (wrapping around the new year)."""
    gap = (series - woy).abs()
    return (gap <= spread) | (gap >= 52 - spread)


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _climate(f, clim, fdate):
    past = clim[clim['weather_week'] < pd.Timestamp(fdate)]
    weeks = [fdate - timedelta(weeks=k) for k in (1, 2, 3, 4)]      # w1 = last week ... w4 = 4 weeks ago
    counts = past.groupby(past['weather_week'].dt.year).size()
    years = [int(y) for y, n in counts.items() if n >= 26]          # years with at least half a year of weeks
    span = f'{years[0]}–{years[-1]}' if years else ''
    out = []
    specs = [('rainfall_lag', 'rain', 'Rainfall'), ('temp_lag', 'temp', 'Temperature'), ('humidity_lag', 'humid', 'Humidity')]
    for col, key, label in specs:
        vals = [_num(f.get(f'{key}_w{k}')) for k in (1, 2, 3, 4)]
        normals = [past[_near_week(past['woy'], w.isocalendar()[1])][col].mean() for w in weeks]
        if any(v is None for v in vals) or any(pd.isna(n) for n in normals):
            continue
        if key == 'rain':
            now, usual = sum(vals), sum(normals)
            pct = (now - usual) / usual * 100 if usual else 0
            level = 'up' if pct >= 15 else 'down' if pct <= -15 else 'same'
            text = (f'{now:.0f} mm over the past 4 weeks — '
                    + (f'{abs(pct):.0f}% {"above" if pct > 0 else "below"} ' if level != 'same' else 'close to ')
                    + f'the usual {usual:.0f} mm for these weeks')
        elif key == 'temp':
            now, usual = sum(vals) / 4, sum(normals) / 4
            diff = now - usual
            level = 'up' if diff >= 0.5 else 'down' if diff <= -0.5 else 'same'
            text = (f'{now:.1f} °C average — '
                    + (f'{abs(diff):.1f} °C {"warmer" if diff > 0 else "cooler"} than ' if level != 'same' else 'close to ')
                    + f'the usual {usual:.1f} °C')
        else:
            now, usual = sum(vals) / 4, sum(normals) / 4
            diff = now - usual
            level = 'up' if diff >= 3 else 'down' if diff <= -3 else 'same'
            text = (f'{now:.0f}% average — '
                    + (f'{abs(diff):.0f} points {"higher" if diff > 0 else "lower"} than ' if level != 'same' else 'close to ')
                    + f'the usual {usual:.0f}%')
        effect = {'up': 'Favors mosquito breeding', 'down': 'Less favorable for mosquitoes', 'same': 'Typical for the season'}[level]
        out.append({'label': label, 'text': text, 'level': level, 'effect': effect})
    return out, span


def _same_week(f, real, fdate):
    hist = real[(real['barangay'] == f.get('barangay')) & (real['week_start'] < pd.Timestamp(fdate))]
    near = hist[_near_week(hist['woy'], fdate.isocalendar()[1])]
    if near.empty:
        return None
    by_year = near.groupby(near['week_start'].dt.year)['case_count'].mean().round(1)
    avg = float(near['case_count'].mean())
    forecast = _num(f.get('ensemble_cases')) or _num(f.get('predicted_cases')) or 0
    if forecast >= avg + 1 and forecast >= avg * 1.3:
        compare = 'above'
    elif forecast <= avg - 1 and forecast <= avg * 0.7:
        compare = 'below'
    else:
        compare = 'similar to'
    return {'years': [{'year': int(y), 'cases': float(c)} for y, c in by_year.items()],
            'avg': round(avg, 1), 'forecast': forecast, 'compare': compare}


def _case_trend(f, real):
    cases = [_num(f.get(f'cases_w{k}')) for k in (4, 3, 2, 1)]       # oldest → newest
    if any(c is None for c in cases):
        return None
    cases = [int(c) for c in cases]
    rises = falls = 0
    for a, b in zip(reversed(cases[:-1]), reversed(cases[1:])):     # walk back from the newest week
        if b > a and not falls:
            rises += 1
        elif b < a and not rises:
            falls += 1
        else:
            break
    if rises >= 2:
        trend, word = 'up', f'Cases rose {rises} weeks in a row'
    elif falls >= 2:
        trend, word = 'down', f'Cases fell {falls} weeks in a row'
    elif cases[-1] > cases[0]:
        trend, word = 'up', 'Cases are higher than 4 weeks ago'
    elif cases[-1] < cases[0]:
        trend, word = 'down', 'Cases are lower than 4 weeks ago'
    else:
        trend, word = 'same', 'Cases have held steady'
    hist = real[real['barangay'] == f.get('barangay')]['case_count']
    usual = round(float(hist.mean()), 1) if not hist.empty else None
    ratio = round(cases[-1] / usual, 1) if usual else None
    return {'cases': cases, 'trend': trend, 'text': word, 'last': cases[-1], 'usual': usual, 'ratio': ratio}


def forecast_insights(f):
    """Everything the Forecast Insights section needs, or None if the history isn't available."""
    try:
        fdate = date.fromisoformat(str(f.get('week_date')))
        clim, real = _history()
    except (OSError, ValueError, KeyError, TypeError):
        return None
    climate, span = _climate(f, clim, fdate)
    return {
        'climate':   climate,
        'span':      span,
        'same_week': _same_week(f, real, fdate),
        'trend':     _case_trend(f, real),
    }



def _recorded_week(real, barangay, day):
    """Recorded case row for the barangay's week that contains `day`, or None."""
    rows = real[(real['barangay'] == barangay)
                & (real['week_start'] <= pd.Timestamp(day))
                & (real['week_start'] > pd.Timestamp(day) - pd.Timedelta(days=7))]
    return None if rows.empty else rows.iloc[0]


def recorded_cases(barangay, week_date):
    """MCHO recorded cases for the 4 weeks before a forecast week (Week −4 … Week −1)."""
    barangay = (barangay or '').strip().capitalize()
    try:
        start = date.fromisoformat(str(week_date))
        _, real = _history()
    except (OSError, ValueError, KeyError, TypeError):
        return {'found': 0, 'weeks': []}
    weeks = []
    for k in (4, 3, 2, 1):
        day = start - timedelta(weeks=k)
        row = _recorded_week(real, barangay, day)
        weeks.append({
            'field': f'cases_w{k}',
            'from':  day.isoformat(),
            'to':    (day + timedelta(days=6)).isoformat(),
            'cases': None if row is None else int(row['case_count']),
        })
    found = sum(w['cases'] is not None for w in weeks)
    last = real[real['barangay'] == barangay]['week_start'].max()
    return {'found': found, 'weeks': weeks,
            'records_end': None if pd.isna(last) else (last + pd.Timedelta(days=6)).date().isoformat()}


def recorded_week_cases(barangay, week_date):
    """MCHO recorded cases for the forecast week itself, or None if it isn't in the records."""
    try:
        day = date.fromisoformat(str(week_date))
        _, real = _history()
    except (OSError, ValueError, KeyError, TypeError):
        return None
    row = _recorded_week(real, (barangay or '').strip().capitalize(), day)
    return None if row is None else int(row['case_count'])