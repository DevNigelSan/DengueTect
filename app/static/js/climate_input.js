// ── DengueTect Climate Input JS ──

// Marikina City coordinates
const LAT = 14.6507;
const LON = 121.1029;

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
}

// Set default date to today
const dateInput = document.getElementById('week_date');
if (dateInput) {
  const today = new Date().toISOString().split('T')[0];
  dateInput.value = today;
}

// Fetch climate data from Open-Meteo
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
    // Calculate 4-week date range ending at selected date
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

    // Split into 4 weekly chunks
    const weeks = [[], [], [], []];
    dates.forEach((d, i) => {
      const weekIdx = Math.min(Math.floor(i / 7), 3);
      weeks[weekIdx].push({ date: d, rainfall: rainfall[i], temp: temp[i], humidity: humidity[i] });
    });

    // Calculate weekly aggregates
    const weeklyRain  = weeks.map(w => w.reduce((s, d) => s + (d.rainfall || 0), 0).toFixed(1));
    const weeklyTemp  = weeks.map(w => (w.reduce((s, d) => s + (d.temp || 0), 0) / w.length).toFixed(1));
    const weeklyHumid = weeks.map(w => (w.reduce((s, d) => s + (d.humidity || 0), 0) / w.length).toFixed(1));

    // Fill form fields (w4=oldest, w1=most recent)
    ['rain_w4','rain_w3','rain_w2','rain_w1'].forEach((name, i) => {
      document.querySelector(`input[name="${name}"]`).value = weeklyRain[i];
    });
    ['temp_w4','temp_w3','temp_w2','temp_w1'].forEach((name, i) => {
      document.querySelector(`input[name="${name}"]`).value = weeklyTemp[i];
    });
    ['humid_w4','humid_w3','humid_w2','humid_w1'].forEach((name, i) => {
      document.querySelector(`input[name="${name}"]`).value = weeklyHumid[i];
    });

    // Build data log
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

// Validate fields before submit
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
  document.querySelector('form') && document.querySelector('form').submit();
});

// Clear red border on focus
document.querySelectorAll('input[type="number"]').forEach(input => {
  input.addEventListener('focus', () => { input.style.borderColor = ''; });
});