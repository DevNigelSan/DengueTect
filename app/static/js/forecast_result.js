// ── DengueTect Forecast Result JS ──

// Animate probability bar on load
window.addEventListener('load', () => {
  const fill = document.querySelector('.prob-fill');
  if (fill) {
    const target = fill.style.width;
    fill.style.width = '0%';
    setTimeout(() => { fill.style.width = target; }, 300);
  }
});