"""Updating the recorded dengue cases from a CHO case file.

Privacy: the uploaded file is read in memory and never saved. Only the barangay and onset-date
columns are loaded, and only weekly case counts per barangay are kept.
"""
import io
import json
from datetime import date, datetime, timedelta

import pandas as pd

from app.ml.database import get_db

TARGET_BARANGAYS = ['Nangka', 'Tumana', 'Malanday']
MAX_FILE_MB = 10
EARLIEST = date(2022, 1, 1)   # CHO barangay records start in 2022
PROVISIONAL_WEEKS = 2         # the newest weeks may still change as late reports come in
MAX_GAP_WEEKS = 4             # a longer gap with no cases anywhere in the city ends the file's period


# ── Reading the file ──

def _pick_columns(names):
    """Find the barangay and onset-date columns, whatever their exact spelling."""
    barangay = onset = None
    for name in names:
        key = str(name).strip().lower()
        if barangay is None and 'barangay' in key and 'current' in key:
            barangay = name
        if onset is None and (key == 'donset' or 'onset' in key):
            onset = name
    if barangay is None:   # fall back to any barangay column
        barangay = next((n for n in names if 'barangay' in str(n).lower()), None)
    city = next((n for n in names if 'current' in str(n).lower() and 'city' in str(n).lower()), None)
    case_id = next((n for n in names if str(n).strip().lower() in ('case id', 'caseid', 'epiid')), None)
    return barangay, onset, city, case_id


def _read_two_columns(data, filename):
    """Load only the barangay and onset columns. Returns (DataFrame, error)."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    try:
        if ext in ('xlsx', 'xls'):
            names = list(pd.read_excel(io.BytesIO(data), nrows=0).columns)
        elif ext == 'csv':
            names = list(pd.read_csv(io.BytesIO(data), nrows=0, encoding='utf-8-sig').columns)
        else:
            return None, 'Please upload the CHO case file as an Excel (.xlsx) or CSV (.csv) file.'
    except Exception:
        return None, 'This file could not be opened. Please check that it is the CHO case file and try again.'

    brgy_col, onset_col, city_col, id_col = _pick_columns(names)
    missing = [label for label, col in (('(Current Address) Barangay', brgy_col), ('DOnset (date of onset)', onset_col))
               if col is None]
    if missing:
        return None, ('The file is missing the column' + ('s ' if len(missing) > 1 else ' ')
                      + ' and '.join(f'"{m}"' for m in missing)
                      + '. Please upload the case file exported from the CHO surveillance records.')

    keep = [brgy_col, onset_col] + ([city_col] if city_col else []) + ([id_col] if id_col else [])
    try:
        if ext in ('xlsx', 'xls'):
            df = pd.read_excel(io.BytesIO(data), usecols=keep)
        else:
            df = pd.read_csv(io.BytesIO(data), usecols=keep, encoding='utf-8-sig')
    except Exception:
        return None, 'This file could not be read. Please check that it is the CHO case file and try again.'
    df = df[keep]
    df.columns = ['barangay', 'onset'] + (['city'] if city_col else []) + (['case_id'] if id_col else [])
    return df, None


def weekly_counts(data, filename):
    """Turn a CHO case file into weekly case counts per barangay.

    Returns (result, error). result = {'weeks': {barangay: {week_start: cases}},
    'first_week', 'last_week', 'rows_used', 'skipped'}.
    """
    df, error = _read_two_columns(data, filename)
    if error:
        return None, error

    # One case can appear on several rows (one per laboratory test): count each case ID once
    repeated = 0
    if 'case_id' in df.columns:
        has_id = df['case_id'].notna() & (df['case_id'].astype(str).str.strip() != '')
        dup = has_id & df['case_id'].astype(str).str.strip().duplicated()
        repeated = int(dup.sum())
        df = df[~dup].drop(columns='case_id')
    df['barangay'] = df['barangay'].astype(str).str.strip().str.title()
    # Other towns have barangays with the same names (e.g. Malanday in San Mateo), so keep
    # Marikina residents only when the file has a city column
    other_town = pd.Series(False, index=df.index)
    if 'city' in df.columns:
        other_town = ~df['city'].astype(str).str.contains('marikina', case=False, na=False)
    df['onset'] = pd.to_datetime(df['onset'], errors='coerce')
    today = pd.Timestamp(date.today())
    dated = df.dropna(subset=['onset'])
    dated = dated[(dated['onset'] >= pd.Timestamp(EARLIEST)) & (dated['onset'] <= today)].copy()
    if dated.empty:
        return None, ('No usable onset dates were found in this file. '
                      'Check that it is the CHO case file and that the DOnset column is filled in.')

    # Monday-to-Sunday weeks, the same as notebook 01
    dated['week'] = dated['onset'].dt.to_period('W').apply(lambda p: p.start_time.date())

    # The period the file covers: the unbroken run of weeks with cases anywhere in the city, counted
    # back from its newest week. A few stray old dates (e.g. a late report from last year) are left
    # out, so they can't overwrite the weeks in between with zeros.
    city_weeks = sorted(set(dated['week']))
    start = city_weeks[-1]
    for earlier in reversed(city_weeks[:-1]):
        if (start - earlier).days > MAX_GAP_WEEKS * 7:
            break
        start = earlier
    first, last = start, city_weeks[-1]

    in_target = df['barangay'].isin(TARGET_BARANGAYS) & ~other_town
    other_town_cases = int((df['barangay'].isin(TARGET_BARANGAYS) & other_town).sum())
    no_date = int((in_target & df['onset'].isna()).sum())
    use = dated[dated['barangay'].isin(TARGET_BARANGAYS) & ~other_town.loc[dated.index] & (dated['week'] >= first)]
    outside = int(in_target.sum()) - no_date - len(use)
    df = use
    if df.empty:
        return None, ('No cases for Nangka, Tumana or Malanday were found in this file. '
                      'Check that it is the CHO case file.')

    weeks = {}
    for brgy in TARGET_BARANGAYS:
        counts = df[df['barangay'] == brgy].groupby('week').size()
        week, series = first, {}
        while week <= last:             # weeks with no cases count as 0
            series[week.isoformat()] = int(counts.get(week, 0))
            week += timedelta(days=7)
        weeks[brgy] = series

    # A file that starts mid-week (e.g. a yearly file starting on Thursday, January 1) only has part of
    # its first week. That week keeps the existing record if there is one, instead of a too-low count.
    partial = first.isoformat() if use['onset'].min().date() > first else None

    return {
        'weeks': weeks,
        'partial_week': partial,
        'first_week': first.isoformat(),
        'last_week': last.isoformat(),
        'rows_used': int(len(df)),
        'skipped': {'no_date': no_date, 'outside_period': outside, 'other_town': other_town_cases,
                    'repeated_rows': repeated},
    }, None


# ── What the system already has ──

def saved_records():
    """Weekly counts uploaded through the app: {(barangay, week_start): cases}."""
    conn = get_db()
    rows = conn.execute('SELECT barangay, week_start, case_count FROM case_records').fetchall()
    conn.close()
    return {(r['barangay'], r['week_start']): r['case_count'] for r in rows}


def current_counts(csv_real):
    """Recorded weekly counts the system uses now: the original CHO data, updated by uploads.

    csv_real: DataFrame of the recorded rows in processed_dataset_extended.csv
    (barangay, week_start, case_count).
    """
    counts = {(b, pd.Timestamp(w).date().isoformat()): int(c)
              for b, w, c in zip(csv_real['barangay'], csv_real['week_start'], csv_real['case_count'])}
    counts.update(saved_records())
    return counts


def _to_write(result, existing, replace_existing=False):
    """The (barangay, week, cases) an upload would write. Weeks already in the records are only
    replaced when asked, and never the partial first week of a file."""
    partial = result.get('partial_week')
    for brgy, series in result['weeks'].items():
        for week, cases in series.items():
            if (brgy, week) in existing and (not replace_existing or week == partial):
                continue
            yield brgy, week, int(cases)


def compare(result, existing):
    """Per barangay: new weeks, and how the file agrees with the weeks already in the records."""
    summary = []
    partial = result.get('partial_week')
    for brgy, series in result['weeks'].items():
        new = overlap = differ = file_total = rec_total = 0
        changes = []
        for week, cases in series.items():
            before = existing.get((brgy, week))
            if before is None:
                new += 1
                continue
            if week == partial:
                continue
            overlap += 1
            file_total += cases
            rec_total += before
            if before != cases:
                differ += 1
                changes.append({'week': week, 'before': before, 'after': cases})
        summary.append({'barangay': brgy, 'new': new, 'overlap': overlap, 'differ': differ,
                        'file_total': file_total, 'rec_total': rec_total,
                        'new_cases': sum(c for w, c in series.items() if (brgy, w) not in existing),
                        'changes': changes[:8], 'more_changes': max(0, len(changes) - 8)})
    return summary


# ── Pending uploads (preview before saving) ──

def create_upload(result, filename, user):
    conn = get_db()
    cur = conn.execute(
        'INSERT INTO case_uploads (uploaded_at, uploaded_by, filename, status, first_week, last_week, '
        'rows_used, counts_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (datetime.now().strftime('%B %d, %Y · %I:%M %p'), user, filename, 'pending',
         result['first_week'], result['last_week'], result['rows_used'],
         json.dumps({'weeks': result['weeks'], 'skipped': result['skipped'],
                     'partial_week': result.get('partial_week')})))
    conn.commit()
    upload_id = cur.lastrowid
    conn.close()
    return upload_id


def get_upload(upload_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM case_uploads WHERE id = ?', (upload_id,)).fetchone()
    conn.close()
    if not row:
        return None
    up = dict(row)
    data = json.loads(up.pop('counts_json') or '{}')
    up['weeks'] = data.get('weeks', {})
    up['skipped'] = data.get('skipped', {})
    up['partial_week'] = data.get('partial_week')
    return up


def recent_uploads(limit=10):
    conn = get_db()
    rows = conn.execute('SELECT id, uploaded_at, uploaded_by, filename, status, first_week, last_week, rows_used '
                        'FROM case_uploads ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_upload(upload_id, existing, replace_existing=False):
    """Write a pending upload's weekly counts. Overlapping weeks are replaced, never added twice."""
    up = get_upload(upload_id)
    if not up or up['status'] != 'pending':
        return None
    rows = list(_to_write(up, existing, replace_existing))
    conn = get_db()
    for brgy, week, cases in rows:
        conn.execute('INSERT OR REPLACE INTO case_records (barangay, week_start, case_count, upload_id) '
                     'VALUES (?, ?, ?, ?)', (brgy, week, cases, upload_id))
    conn.execute("UPDATE case_uploads SET status = 'saved' WHERE id = ?", (upload_id,))
    conn.commit()
    conn.close()
    return up


def cancel_upload(upload_id):
    conn = get_db()
    conn.execute("UPDATE case_uploads SET status = 'cancelled', counts_json = NULL "
                 "WHERE id = ? AND status = 'pending'", (upload_id,))
    conn.commit()
    conn.close()


def provisional_from(last_week):
    """First week that may still change (the newest PROVISIONAL_WEEKS weeks)."""
    if not last_week:
        return None
    return (date.fromisoformat(last_week) - timedelta(weeks=PROVISIONAL_WEEKS - 1)).isoformat()


# ── Heatmap: add uploaded weeks to the notebook's heatmap.json ──

def merge_into_heatmap(heatmap_data):
    """Append uploaded weeks after the heatmap's last week and update recorded weeks it already has.

    The risk colour of a new week follows the heatmap's own rule: the risk already shown for weeks
    with the same case count in that barangay (higher counts than ever seen count as high).
    """
    records = saved_records()
    if not records:
        return heatmap_data
    barangays = heatmap_data.get('barangays', {})
    for brgy, weeks in barangays.items():
        by_cases = {}
        for e in weeks:
            if e.get('source') != 'synthetic':
                by_cases.setdefault(int(e['cases']), {}).setdefault(e.get('risk', 'none'), 0)
                by_cases[int(e['cases'])][e.get('risk', 'none')] += 1
        top = max(by_cases) if by_cases else 0

        def risk_for(cases):
            if cases == 0:
                return 'none'
            if cases in by_cases:
                return max(by_cases[cases], key=by_cases[cases].get)
            if cases > top:
                return 'high'
            lower = [k for k in by_cases if 0 < k < cases]
            return risk_for(max(lower)) if lower else 'low'

        index = {e['week']: e for e in weeks}
        for (b, week), cases in sorted(records.items()):
            if b != brgy:
                continue
            if week in index:
                if index[week].get('source') != 'synthetic':
                    index[week]['cases'] = cases
                    index[week]['risk'] = risk_for(cases)
            elif not weeks or week > weeks[-1]['week']:
                entry = {'week': week, 'cases': cases, 'source': 'real', 'risk': risk_for(cases)}
                weeks.append(entry)
                index[week] = entry
    all_cases = [e['cases'] for w in barangays.values() for e in w]
    if all_cases:
        heatmap_data['max_cases'] = max(heatmap_data.get('max_cases', 0), max(all_cases))
    return heatmap_data