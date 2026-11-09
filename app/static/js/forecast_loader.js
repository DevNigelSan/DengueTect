// ── DengueTect Forecast Loader ──
// Shows a loading screen while the forecast runs.
// Its styles are built in here, so it looks right on every page and server.

(function () {
  const css = `
    #forecast-loader{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;
      padding:16px;background:rgba(13,59,122,.88);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px)}
    #forecast-loader .loader-box{text-align:center;max-width:420px}
    #forecast-loader .loader-ekg{display:block;width:220px;height:70px;margin:0 auto 22px;overflow:visible}
    #forecast-loader .loader-ekg path{fill:none;stroke:#60C8FF;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;
      stroke-dasharray:400;stroke-dashoffset:400;animation:dtDrawEkg 1.6s ease-in-out infinite;
      filter:drop-shadow(0 0 6px rgba(96,200,255,.6))}
    #forecast-loader .loader-label{font-family:'DM Sans',sans-serif;font-size:22px;font-weight:700;color:#FFFFFF;margin-bottom:8px}
    #forecast-loader .loader-sub{font-family:'Inter',sans-serif;font-size:15px;line-height:1.5;color:rgba(255,255,255,.85)}
    @keyframes dtDrawEkg{0%{stroke-dashoffset:400}60%{stroke-dashoffset:0}100%{stroke-dashoffset:-400}}
    @media (prefers-reduced-motion: reduce){#forecast-loader .loader-ekg path{animation:none;stroke-dashoffset:0}}
  `;
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  function showLoader() {
    if (document.getElementById('forecast-loader')) return;
    const overlay = document.createElement('div');
    overlay.id = 'forecast-loader';
    overlay.setAttribute('role', 'status');
    overlay.setAttribute('aria-live', 'polite');
    overlay.innerHTML = `
      <div class="loader-box">
        <svg class="loader-ekg" viewBox="0 0 200 60" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0,30 L40,30 L55,30 L60,10 L65,50 L70,5 L77,45 L82,30 L120,30 L160,30 L200,30"/>
        </svg>
        <div class="loader-label">Running the forecast…</div>
        <div class="loader-sub">Estimating next week's cases and the chance of an outbreak.<br>This can take a few seconds.</div>
      </div>`;
    document.body.appendChild(overlay);
  }

  function hideLoader() {
    const overlay = document.getElementById('forecast-loader');
    if (overlay) overlay.remove();
  }

  // Show it when the forecast form is actually sent (not when a field is still empty)
  const submitBtn = document.getElementById('submitBtn');
  const form = submitBtn ? submitBtn.form || submitBtn.closest('form') : null;
  if (form) {
    form.addEventListener('submit', e => {
      setTimeout(() => { if (!e.defaultPrevented) showLoader(); }, 0);
    });
  }

  // Coming back with the browser's Back button: don't leave the loading screen stuck
  window.addEventListener('pageshow', hideLoader);
})();