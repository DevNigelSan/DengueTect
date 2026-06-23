// ── DengueTect Dashboard JS ──

const barangayData = {
  nangka: {
    cases: 47,
    probability: 82,
    risk: 'high',
    riskLabel: 'HIGH RISK — Barangay Nangka',
    riskDesc: 'Outbreak probability exceeds 75%. Immediate response recommended.',
    rainfall: '182', temp: '31.4', humidity: '87',
    rainWidth: '73%', tempWidth: '63%', humidWidth: '87%'
  },
  tumana: {
    cases: 28,
    probability: 61,
    risk: 'moderate',
    riskLabel: 'MODERATE RISK — Barangay Tumana',
    riskDesc: 'Elevated probability detected. Increase surveillance activities.',
    rainfall: '165', temp: '30.8', humidity: '83',
    rainWidth: '66%', tempWidth: '58%', humidWidth: '83%'
  },
  malanday: {
    cases: 14,
    probability: 33,
    risk: 'low',
    riskLabel: 'LOW RISK — Barangay Malanday',
    riskDesc: 'Risk within normal range. Continue routine monitoring.',
    rainfall: '140', temp: '30.1', humidity: '79',
    rainWidth: '56%', tempWidth: '52%', humidWidth: '79%'
  }
};

function updateDashboard(barangay) {
  const d = barangayData[barangay];
  if (!d) return;

  // alert banner
  const banner = document.getElementById('alertBanner');
  banner.className = 'alert-tier-bar ' + d.risk;
  document.getElementById('tierTitle').textContent = d.riskLabel;
  document.getElementById('tierDesc').textContent  = d.riskDesc;
  document.getElementById('tierPill').textContent  = d.risk.toUpperCase();

  // forecast cards
  document.getElementById('caseCount').textContent = d.cases;
  document.getElementById('probValue').innerHTML =
    d.probability + '<span class="fcard-unit">%</span>';

  const fill = document.getElementById('riskFill');
  fill.style.width = d.probability + '%';
  fill.className = 'risk-fill ' + d.risk;

  // climate
  document.getElementById('rainfallVal').innerHTML = d.rainfall + '<span>mm</span>';
  document.getElementById('tempVal').innerHTML     = d.temp + '<span>°C</span>';
  document.getElementById('humidVal').innerHTML    = d.humidity + '<span>%</span>';

  document.querySelectorAll('.climate-fill')[0].style.width = d.rainWidth;
  document.querySelectorAll('.climate-fill')[1].style.width = d.tempWidth;
  document.querySelectorAll('.climate-fill')[2].style.width = d.humidWidth;

  // active barangay label
  const name = barangay.charAt(0).toUpperCase() + barangay.slice(1);
  document.getElementById('activeBrgy').textContent  = name;
  document.getElementById('tableBregy').textContent  = 'Barangay ' + name;
}

// tab switching
document.querySelectorAll('.btab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.btab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    updateDashboard(tab.dataset.barangay);
  });
});