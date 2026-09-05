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

// Clear all form fields
function clearForm() {
  document.querySelectorAll('input[type="number"]').forEach(input => {
    input.value = '';
  });
  document.getElementById('barangay').value = '';
  document.getElementById('week_date').value = '';
  document.getElementById('fetchStatus').innerHTML = '';
  document.getElementById('logCard').style.display = 'none';
  document.getElementById('logContent').innerHTML = '';
  document.querySelector('.cases-row').classList.remove('has-warning');
  document.querySelectorAll('.case-warn').forEach(w => w.remove());
}

// Set default date to today
const dateInput = document.getElementById('week_date');
if (dateInput) {
  const today = new Date().toISOString().split('T')[0];
  dateInput.value = today;
}

// ── CASE COUNT VALIDATION ──
function validateCaseInput(input) {
  const val = parseInt(input.value);
  const existingWarn = input.parentElement.querySelector('.case-warn');
  if (existingWarn) existingWarn.remove();

  const casesRow = document.querySelector('.cases-row');

  // Check if any case input is over 50
  const anyOver50 = Array.from(
    document.querySelectorAll('input[name^="cases_"]')
  ).some(i => parseInt(i.value) > 50);

  if (anyOver50) {
    casesRow.classList.add('has-warning');
  } else {
    casesRow.classList.remove('has-warning');
  }

  if (isNaN(val) || val <= 50) return;

  if (val > 50 && val <= 100) {
    const warn = document.createElement('div');
    warn.className = 'case-warn';
    warn.textContent = '⚠️ Unusually high — please verify this value.';
    input.parentElement.appendChild(warn);
  }
}

document.querySelectorAll('input[name^="cases_"]').forEach(input => {
  input.addEventListener('blur', () => validateCaseInput(input));
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
    const endDate   = new Date(weekDate);
    const startDate = new Date(weekDate);
    startDate.setDate(startDate.getDate() - 28);

    const start = startDate.toISOString().split('T')[0];
    const end   = endDate.toISOString().split('T')[0];

    const url = `https://archive-api.open-meteo.com/v1/archive?latitude=${LAT}&longitude=${LON}&start_date=${start}&end_date=${end}&daily=precipitation_sum,temperature_2m_mean,relative_humidity_2m_mean&timezone=Asia/Manila`;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!data.daily) {
      showStatus('error', 'Failed to fetch data. Try a different date.');
      return;
    }

    const dates    = data.daily.time;
    const rainfall = data.daily.precipitation_sum;
    const temp     = data.daily.temperature_2m_mean;
    const humidity = data.daily.relative_humidity_2m_mean;

    const weeks = [[], [], [], []];
    dates.forEach((d, i) => {
      const weekIdx = Math.min(Math.floor(i / 7), 3);
      weeks[weekIdx].push({ date: d, rainfall: rainfall[i], temp: temp[i], humidity: humidity[i] });
    });

    const weeklyRain  = weeks.map(w => w.reduce((s, d) => s + (d.rainfall || 0), 0).toFixed(1));
    const weeklyTemp  = weeks.map(w => (w.reduce((s, d) => s + (d.temp || 0), 0) / w.length).toFixed(1));
    const weeklyHumid = weeks.map(w => (w.reduce((s, d) => s + (d.humidity || 0), 0) / w.length).toFixed(1));

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
    showStatus('success', `Data fetched successfully for ${start} to ${end}.`);

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
    const dateRange = week.length > 0
      ? `${week[0].date} → ${week[week.length-1].date}`
      : '—';

    html += `
      <div class="log-week">
        <div class="log-week-header">
          <span class="log-week-label">${labels[i]}</span>
          <span class="log-week-dates">${dateRange}</span>
        </div>
        <div class="log-week-vals">
          <div class="log-val-item">
            <span class="log-val-label">Rainfall</span>
            <span class="log-val-num rain">${rain[i]} mm</span>
            <span class="log-val-note">sum of ${week.length} days</span>
          </div>
          <div class="log-val-item">
            <span class="log-val-label">Temperature</span>
            <span class="log-val-num temp">${temp[i]} °C</span>
            <span class="log-val-note">avg of ${week.length} days</span>
          </div>
          <div class="log-val-item">
            <span class="log-val-label">Humidity</span>
            <span class="log-val-num humid">${humid[i]} %</span>
            <span class="log-val-note">avg of ${week.length} days</span>
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
    .filter(i => parseInt(i.value) > 100);

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