// ── DengueTect Forecast Loader ──
// Shows a loading overlay when the forecast form is submitted

function showLoader() {
  const overlay = document.createElement('div');
  overlay.id = 'forecast-loader';
  overlay.innerHTML = `
    <div class="loader-box">
      <svg class="loader-ekg" viewBox="0 0 200 60" preserveAspectRatio="none">
        <path d="M0,30 L40,30 L55,30 L60,10 L65,50 L70,5 L77,45 L82,30 L120,30 L160,30 L200,30"/>
      </svg>
      <div class="loader-label">Running forecast models...</div>
      <div class="loader-sub">Random Forest · Logistic Regression</div>
    </div>
  `;
  document.body.appendChild(overlay);
}

// attach to forecast submit button if present
const submitBtn = document.getElementById('submitBtn');
if (submitBtn) {
  submitBtn.addEventListener('click', () => {
    const barangay = document.getElementById('barangay')?.value;
    const weekDate = document.getElementById('week_date')?.value;
    const numbers  = document.querySelectorAll('input[type="number"]');
    let allFilled  = barangay && weekDate;

    numbers.forEach(n => { if (!n.value) allFilled = false; });
    if (allFilled) showLoader();
  });
}