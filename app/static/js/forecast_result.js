// ── DengueTect Forecast Result JS ──

// Auto-set report generated timestamp
const now = new Date();
const options = {
  year: 'numeric', month: 'long', day: 'numeric',
  hour: '2-digit', minute: '2-digit'
};
const formatted = now.toLocaleDateString('en-PH', options);

const genTime = document.querySelector('.report-meta-val');
if (genTime) genTime.textContent = formatted;

// Animate probability bar on load
window.addEventListener('load', () => {
  const fill = document.querySelector('.prob-fill');
  if (fill) {
    const target = fill.style.width;
    fill.style.width = '0%';
    setTimeout(() => { fill.style.width = target; }, 300);
  }
});