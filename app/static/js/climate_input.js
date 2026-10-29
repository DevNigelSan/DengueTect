// ── DengueTect Climate Input JS ──

// Marikina City coordinates
const LAT = 14.6507;
const LON = 121.1029;

// Week labels for user-friendly display
const WEEK_LABELS = {
  'cases_w4': 'Week −4 (oldest)',
  'cases_w3': 'Week −3',
  'cases_w2': 'Week −2',
  'cases_w1': 'Week −1 (most recent)'
};

// ── PARAMETER BASELINES ──
const BASELINES = {
  rain: {
    moderate: 56,
    high: 84,
    alarming: 123,
    max: 250,
    unit: 'mm',
    labels: { normal: '0–55mm Normal', moderate: '56–83mm Elevated', high: '84–122mm High', alarming: '123mm+ Alarming' }
  },
  temp: {
    moderate: 27.4,
    high: 28.7,
    alarming: 31.7,
    max: 35,
    unit: '°C',
    labels: { normal: 'Below 27.4°C Normal', moderate: '27.4–28.7°C Elevated', high: 'Above 28.7°C Alarming', alarming: 'Above 28.7°C Alarming' }
  },
  humid: {
    moderate: 86.9,
    high: 88.6,
    alarming: 91.3,
    max: 100,
    unit: '%',
    labels: { normal: 'Below 86.9% Normal', moderate: '86.9–88.6% Elevated', high: 'Above 88.6% Alarming', alarming: 'Above 88.6% Alarming' }
  }
};

function getParamType(name) {
  if (name.startsWith('rain')) return 'rain';
  if (name.startsWith('temp')) return 'temp';
  if (name.startsWith('humid')) return 'humid';
  return null;
}

function resetParamRow(row) {
  row.style.borderColor = '';
  row.style.background  = '';
  row.style.boxShadow   = '';
  const indicator = row.querySelector('.param-indicator');
  if (indicator) indicator.remove();
}

function updateParamIndicator(input) {
  const type = getParamType(input.name);
  if (!type) return;

  const val      = parseFloat(input.value);
  const base     = BASELINES[type];
    const row      = input.closest('.climate-input-row');
  if (!row) return;
  if (isNaN(val)) {
    // Field was emptied: clear the colour only if the whole row is empty
    const anyFilled = Array.from(row.querySelectorAll('input')).some(i => i.value !== '');
    if (!anyFilled) resetParamRow(row);
    return;
  }

  let level, color, bgColor, borderColor, label;

  if (type === 'rain') {
    if (val >= base.alarming) {
      level = 'alarming'; color = '#991B1B'; bgColor = '#FEE2E2'; borderColor = '#DC2626';
      label = base.labels.alarming;
    } else if (val >= base.high) {
      level = 'high'; color = '#C2410C'; bgColor = '#FFEDD5'; borderColor = '#F97316';
      label = base.labels.high;
    } else if (val >= base.moderate) {
      level = 'moderate'; color = '#92400E'; bgColor = '#FEF3C7'; borderColor = '#F59E0B';
      label = base.labels.moderate;
    } else {
      level = 'normal'; color = '#166534'; bgColor = '#F0FDF4'; borderColor = '#86EFAC';
      label = base.labels.normal;
    }
  } else {
    if (val >= base.high) {
      level = 'alarming'; color = '#991B1B'; bgColor = '#FEE2E2'; borderColor = '#DC2626';
      label = base.labels.alarming;
    } else if (val >= base.moderate) {
      level = 'moderate'; color = '#92400E'; bgColor = '#FEF3C7'; borderColor = '#F59E0B';
      label = base.labels.moderate;
    } else {
      level = 'normal'; color = '#166534'; bgColor = '#F0FDF4'; borderColor = '#86EFAC';
      label = base.labels.normal;
    }
  }

  // Update row styling
  row.style.borderColor = borderColor;
  row.style.background  = bgColor;
  row.style.boxShadow   = `0 0 20px ${borderColor}55, 0 0 40px ${borderColor}22`;

  // Update or create indicator label
  let indicator = row.querySelector('.param-indicator');
  if (!indicator) {
    indicator = document.createElement('div');
    indicator.className = 'param-indicator';
    row.appendChild(indicator);
  }
  indicator.textContent = label;
  indicator.style.color = color;
  indicator.style.background = bgColor;
  indicator.style.borderColor = borderColor;
}

// Attach listeners to climate inputs
['rain', 'temp', 'humid'].forEach(type => {
  ['w1','w2','w3','w4'].forEach(week => {
    const input = document.querySelector(`input[name="${type}_${week}"]`);
    if (input) {
      input.addEventListener('input', () => updateParamIndicator(input));
      input.addEventListener('blur',  () => updateParamIndicator(input));
    }
  });
});

// Also trigger on fetch
const origBuildLog = window.buildLog;

// Clear all form fields
function clearForm() {
  document.querySelectorAll('input[type="number"]').forEach(input => {
    input.value = '';
  });
  document.getElementById('barangay').value = '';
  document.getElementById('week_date').value = '';
  checkWeekTiming();

  const status = document.getElementById('fetchStatus');
  status.innerHTML = '';
  status.className = 'fetch-status';

  document.getElementById('logCard').style.display = 'none';
  document.getElementById('logContent').innerHTML = '';

  // Remove the rainfall / temperature / humidity colour states
  document.querySelectorAll('.climate-input-row').forEach(resetParamRow);

  document.querySelector('.cases-row').classList.remove('has-warning');
  document.querySelectorAll('input[name^="cases_"]').forEach(i => { delete i.dataset.auto; });
  showCasesSource('', '');
  validateCases();
}

// Set default date to today
const dateInput = document.getElementById('week_date');
if (dateInput) {
  const today = new Date().toISOString().split('T')[0];
  dateInput.value = today;
}

// ── CASE COUNT VALIDATION ──
// Thresholds match the "?" popup: mean + 1 SD and mean + 2 SD of weekly cases (2022–2026)
const CASE_WARN    = 7;   // unusually high → highlight and ask to verify
const CASE_CONFIRM = 9;   // rare → must confirm before running the forecast

function validateCases() {
  const casesRow = document.querySelector('.cases-row');
  const inputs   = Array.from(document.querySelectorAll('input[name^="cases_"]'));
  const flagged  = [];

  inputs.forEach(input => {
    const val = parseInt(input.value);
    input.classList.remove('case-high', 'case-very-high');
    if (isNaN(val)) return;
    if (val >= CASE_CONFIRM) {
      input.classList.add('case-very-high');
      flagged.push(`${WEEK_LABELS[input.name]}: ${val}`);
    } else if (val >= CASE_WARN) {
      input.classList.add('case-high');
      flagged.push(`${WEEK_LABELS[input.name]}: ${val}`);
    }
  });

  casesRow.classList.toggle('has-warning', flagged.length > 0);

  let note = casesRow.querySelector('.case-note');
  if (!flagged.length) {
    if (note) note.remove();
    return;
  }
  if (!note) {
    note = document.createElement('div');
    note.className = 'case-note';
    casesRow.appendChild(note);
  }

  const needsConfirm = inputs.some(i => parseInt(i.value) >= CASE_CONFIRM);
  note.innerHTML = `<strong>Higher than usual</strong> (${flagged.join(' · ')}). Please double-check your CHO records.`
    + (needsConfirm ? ` Values of ${CASE_CONFIRM} or more will need confirmation before the forecast runs.` : '');
}

document.querySelectorAll('input[name^="cases_"]').forEach(input => {
  input.addEventListener('input', validateCases);
  input.addEventListener('blur',  validateCases);
});

// ── CUSTOM MODAL ──
function showCaseModal(highCases, onConfirm) {
  const overlay = document.createElement('div');
  overlay.className = 'case-modal-overlay';

  const entries = highCases.map(i => `
    <div class="case-modal-entry">
      <span class="case-modal-entry-label">${WEEK_LABELS[i.name] || i.name}</span>
      <span class="case-modal-entry-val">${i.value} cases</span>
    </div>
  `).join('');

  overlay.innerHTML = `
    <div class="case-modal">
      <div class="case-modal-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </div>
      <div class="case-modal-title">High Case Count Detected</div>
      <div class="case-modal-desc">
        The following weeks have unusually high dengue case counts. Please double-check your records before proceeding.
      </div>
      <div class="case-modal-entries">${entries}</div>
      <div class="case-modal-note">
        If these numbers are correct based on your official CHO records, you may proceed. Otherwise, click <strong>Go Back</strong> to correct the values.
      </div>
      <div class="case-modal-actions">
        <button class="case-modal-cancel" id="modalCancel">Go Back</button>
        <button class="case-modal-confirm" id="modalConfirm">Yes, Proceed</button>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  document.getElementById('modalCancel').addEventListener('click', () => {
    overlay.remove();
  });

  document.getElementById('modalConfirm').addEventListener('click', () => {
    overlay.remove();
    onConfirm();
  });
}

// ── OPEN METEO FETCH ──

// Local date → 'YYYY-MM-DD' (avoids time-zone shifts changing the day)
function toISODate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

async function fetchClimateData() {
  const weekDate = document.getElementById('week_date').value;
  if (!weekDate) {
    showStatus('error', 'Please select a week date first.');
    return;
  }

  const fetchBtn = document.getElementById('fetchBtn');
  fetchBtn.disabled = true;
  fetchBtn.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spin">
      <polyline points="1 4 1 10 7 10"/>
      <path d="M3.51 15a9 9 0 1 0 .49-3.43"/>
    </svg>
    Fetching...`;

  try {
    // The 4 full weeks (28 days) BEFORE the selected week
    const weekStart = new Date(weekDate + 'T00:00:00');
    const dates = [];
    for (let i = 28; i >= 1; i--) {
      const d = new Date(weekStart);
      d.setDate(d.getDate() - i);
      dates.push(toISODate(d));
    }
    const start = dates[0];
    const end   = dates[dates.length - 1];

    const url = `https://archive-api.open-meteo.com/v1/archive?latitude=${LAT}&longitude=${LON}&start_date=${start}&end_date=${end}&daily=precipitation_sum,temperature_2m_mean,relative_humidity_2m_mean&timezone=Asia/Manila`;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!data.daily) {
      showStatus('error', data.reason
        ? `The weather archive couldn't provide this range. Try an earlier date.`
        : 'Failed to fetch data. Try a different date.');
      return;
    }

    // Look up each day's readings by date; days the archive doesn't have stay null
    const byDate = {};
    data.daily.time.forEach((d, i) => {
      byDate[d] = {
        rainfall: data.daily.precipitation_sum[i],
        temp:     data.daily.temperature_2m_mean[i],
        humidity: data.daily.relative_humidity_2m_mean[i]
      };
    });

    // Exactly 7 days per week: index 0 = Week −4 (oldest) … 3 = Week −1 (most recent)
    const weeks = [0, 1, 2, 3].map(w =>
      dates.slice(w * 7, w * 7 + 7).map(d => ({ date: d, ...(byDate[d] || {}) }))
    );

    // Only real readings count — missing days are skipped, never treated as 0
    const readings = (week, key) => week.map(d => d[key]).filter(v => v !== null && v !== undefined);
    const total    = vals => vals.reduce((s, v) => s + v, 0);

    const weeklyRain  = weeks.map(w => { const v = readings(w, 'rainfall'); return v.length ? total(v).toFixed(1) : ''; });
    const weeklyTemp  = weeks.map(w => { const v = readings(w, 'temp');     return v.length ? (total(v) / v.length).toFixed(1) : ''; });
    const weeklyHumid = weeks.map(w => { const v = readings(w, 'humidity'); return v.length ? (total(v) / v.length).toFixed(1) : ''; });

    ['rain_w4','rain_w3','rain_w2','rain_w1'].forEach((name, i) => {
      document.querySelector(`input[name="${name}"]`).value = weeklyRain[i];
    });
    ['temp_w4','temp_w3','temp_w2','temp_w1'].forEach((name, i) => {
      document.querySelector(`input[name="${name}"]`).value = weeklyTemp[i];
    });
    ['humid_w4','humid_w3','humid_w2','humid_w1'].forEach((name, i) => {
      document.querySelector(`input[name="${name}"]`).value = weeklyHumid[i];
    });

    buildLog(weeks, weeklyRain, weeklyTemp, weeklyHumid, start, end);

    const missingDays = weeks.reduce((s, w) => s + (7 - readings(w, 'temp').length), 0);
    if (missingDays === 0) {
      showStatus('success', `Data fetched for ${start} to ${end}.`);
    } else {
      showStatus('warning', `${missingDays} day${missingDays !== 1 ? 's' : ''} in this range ${missingDays !== 1 ? 'are' : 'is'} not in the weather archive yet. Check the marked weeks in the log, fill in any empty boxes, or pick an earlier date.`);
    }

    // Update parameter indicators after fetch
         document.querySelectorAll('input[name^="rain_"], input[name^="temp_"], input[name^="humid_"]').forEach(input => {
      updateParamIndicator(input);
    });
    loadRecordedCases();
    

  } catch (err) {
    showStatus('error', 'Network error. Check your connection and try again.');
    console.error(err);
  } finally {
    fetchBtn.disabled = false;
    fetchBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="1 4 1 10 7 10"/>
        <path d="M3.51 15a9 9 0 1 0 .49-3.43"/>
      </svg>
      Fetch Climate Data`;
  }
}

function buildLog(weeks, rain, temp, humid, start, end) {
  const logCard    = document.getElementById('logCard');
  const logContent = document.getElementById('logContent');
  logCard.style.display = 'block';

  const labels = ['Week −4', 'Week −3', 'Week −2', 'Week −1'];

  let html = '';
  weeks.forEach((week, i) => {
    const dateRange = `${week[0].date} → ${week[week.length - 1].date}`;
    const days      = week.filter(d => d.temp !== null && d.temp !== undefined).length;
    const noteClass = days < 7 ? 'log-val-note incomplete' : 'log-val-note';
    const shown     = (v, unit) => v === '' ? '—' : `${v} ${unit}`;

    html += `
      <div class="log-week">
        <div class="log-week-header">
          <span class="log-week-label">${labels[i]}</span>
          <span class="log-week-dates">${dateRange}</span>
        </div>
        <div class="log-week-vals">
          <div class="log-val-item">
            <span class="log-val-label">Rainfall</span>
            <span class="log-val-num rain">${shown(rain[i], 'mm')}</span>
            <span class="${noteClass}">sum of ${days} of 7 days</span>
          </div>
          <div class="log-val-item">
            <span class="log-val-label">Temperature</span>
            <span class="log-val-num temp">${shown(temp[i], '°C')}</span>
            <span class="${noteClass}">avg of ${days} of 7 days</span>
          </div>
          <div class="log-val-item">
            <span class="log-val-label">Humidity</span>
            <span class="log-val-num humid">${shown(humid[i], '%')}</span>
            <span class="${noteClass}">avg of ${days} of 7 days</span>
          </div>
        </div>
      </div>`;
  });

  logContent.innerHTML = html;
}

function showStatus(type, msg) {
  const el = document.getElementById('fetchStatus');
  el.className = `fetch-status ${type}`;
  el.textContent = msg;
}

// ── FORM SUBMIT ──
document.getElementById('submitBtn').addEventListener('click', function(e) {
  e.preventDefault();

  const barangay = document.getElementById('barangay').value;
  const weekDate = document.getElementById('week_date').value;
  const numbers  = document.querySelectorAll('input[type="number"]');

  let valid = true;

  if (!barangay) { alert('Please select a barangay.'); valid = false; }
  if (!weekDate) { alert('Please select a week date.'); valid = false; }

  numbers.forEach(input => {
    if (input.value === '' || isNaN(input.value)) {
      input.style.borderColor = '#DC2626';
      valid = false;
    } else {
      input.style.borderColor = '';
    }
  });

  if (!valid) return;

  // Check for case values over 100
    const highCases = Array.from(document.querySelectorAll('input[name^="cases_"]'))
    .filter(i => parseInt(i.value) >= CASE_CONFIRM);

  if (highCases.length > 0) {
    showCaseModal(highCases, () => {
      document.querySelector('form').submit();
    });
    return;
  }

  document.querySelector('form') && document.querySelector('form').submit();
});

// Clear red border on focus
document.querySelectorAll('input[type="number"]').forEach(input => {
  input.addEventListener('focus', () => { input.style.borderColor = ''; });
});

// Cases info popup
function toggleCasesInfo(event) {
  event.stopPropagation();
  const overlay = document.getElementById('casesInfoOverlay');
  overlay.style.display = overlay.style.display === 'none' ? 'flex' : 'none';
}

// Close when clicking overlay background
document.getElementById('casesInfoOverlay').addEventListener('click', function(e) {
  if (e.target === this) this.style.display = 'none';
});


// ── RECORDED CASES (MCHO records) ──
// When the barangay and week are set, fill the 4 case boxes from the recorded data if it exists
async function loadRecordedCases() {
  const barangay = document.getElementById('barangay').value;
  const weekDate = document.getElementById('week_date').value;
  if (!barangay || !weekDate) { showCasesSource('', ''); return; }

  try {
    const resp = await fetch(`/api/recorded-cases?barangay=${encodeURIComponent(barangay)}&week=${encodeURIComponent(weekDate)}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    data.weeks.forEach(w => {
      const input = document.querySelector(`input[name="${w.field}"]`);
      if (!input) return;
      if (w.cases !== null) {
        input.value = w.cases;
        input.dataset.auto = '1';
        input.style.borderColor = '';
      } else if (input.dataset.auto === '1') {
        input.value = '';                 // clear values that came from an earlier lookup
        delete input.dataset.auto;
      }
    });

    if (data.found === 4) {
      showCasesSource('ok', `Filled from MCHO records (${data.weeks[0].from} to ${data.weeks[3].to}). You can still edit them.`);
    } else if (data.found > 0) {
      const left = 4 - data.found;
      showCasesSource('partial', `${data.found} of 4 weeks filled from MCHO records. Enter the empty week${left > 1 ? 's' : ''} from your latest surveillance report.`);
    } else {
      showCasesSource('none', `No recorded cases for these weeks${data.records_end ? ` (records end ${data.records_end})` : ''}. Please enter them from your latest surveillance report.`);
    }
    validateCases();
  } catch (err) {
    console.error(err);
    showCasesSource('', '');
  }
}

function showCasesSource(type, msg) {
  let el = document.getElementById('casesSource');
  if (!el) {
    el = document.createElement('div');
    el.id = 'casesSource';
    document.querySelector('.cases-row').insertAdjacentElement('afterend', el);
  }
  el.className = `cases-source ${type}`;
  el.textContent = msg;
  el.hidden = !msg;
}

// A value typed by hand no longer comes from the records
document.querySelectorAll('input[name^="cases_"]').forEach(input => {
  input.addEventListener('input', () => { delete input.dataset.auto; });
});

document.getElementById('barangay').addEventListener('change', loadRecordedCases);
document.getElementById('week_date').addEventListener('change', loadRecordedCases);


// ── PAST / FUTURE WEEK WARNING ──
// Warn when the forecast week is not the current week
function mondayOf(d) {
  const m = new Date(d);
  m.setHours(0, 0, 0, 0);
  m.setDate(m.getDate() - ((m.getDay() + 6) % 7));
  return m;
}

function checkWeekTiming() {
  const input = document.getElementById('week_date');
  let el = document.getElementById('weekWarning');
  if (!el) {
    el = document.createElement('div');
    el.id = 'weekWarning';
    el.className = 'week-warning';
    el.setAttribute('role', 'status');
    input.closest('.field-row').insertAdjacentElement('afterend', el);
  }
  if (!input.value) { el.hidden = true; return; }

  const weeks = Math.round((mondayOf(new Date(input.value + 'T00:00:00')) - mondayOf(new Date())) / (7 * 864e5));
  if (weeks === 0) { el.hidden = true; return; }

  const n = Math.abs(weeks);
  const span = `${n} week${n !== 1 ? 's' : ''}`;
  el.innerHTML = weeks < 0
    ? `<span><strong>This is a past week</strong> (${span} ago). The forecast will be saved in History for review, but the Dashboard will keep showing a newer forecast if one exists.</span>`
    : `<span><strong>This week hasn't started yet</strong> (${span} ahead). Climate data for it may not be available yet, so check the values before running the forecast.</span>`;
  el.hidden = false;
}

document.getElementById('week_date').addEventListener('change', checkWeekTiming);
document.getElementById('week_date').addEventListener('input', checkWeekTiming);
checkWeekTiming();