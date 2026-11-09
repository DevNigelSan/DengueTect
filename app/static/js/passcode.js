// ── DengueTect: office passcode before publishing ──
// Any form with data-passcode asks for the passcode first; the server checks it.

(function () {
  const css = `
    .pc-overlay{position:fixed;inset:0;z-index:2000;display:flex;align-items:center;justify-content:center;
      padding:16px;background:rgba(15,23,42,.55)}
    .pc-overlay[hidden]{display:none}
    .pc-box{width:100%;max-width:420px;background:var(--white,#fff);color:var(--gray-800,#1E293B);
      border:1.5px solid var(--gray-200,#E2E8F0);border-radius:16px;padding:24px;box-shadow:0 20px 50px rgba(0,0,0,.25);
      font-family:'Inter',system-ui,sans-serif}
    .pc-head{display:flex;gap:12px;align-items:center;margin-bottom:10px}
    .pc-icon{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;
      background:var(--blue-light,#DBEAFE);color:var(--blue-primary,#1A56A0);flex-shrink:0}
    .pc-title{font-family:'DM Sans',sans-serif;font-size:19px;font-weight:700;color:var(--blue-deep,#0D3B7A)}
    .pc-text{font-size:14.5px;line-height:1.55;color:var(--gray-600,#475569);margin-bottom:14px}
    .pc-label{display:block;font-size:14px;font-weight:600;margin-bottom:6px}
    .pc-row{display:flex;gap:8px}
    .pc-input{flex:1;min-width:0;height:50px;padding:0 14px;font-size:18px;letter-spacing:2px;
      border:2px solid var(--gray-400,#94A3B8);border-radius:10px;background:var(--white,#fff);color:inherit}
    .pc-input:focus{outline:none;border-color:var(--blue-primary,#1A56A0);box-shadow:0 0 0 3px rgba(26,86,160,.2)}
    .pc-show{height:50px;padding:0 12px;border-radius:10px;border:2px solid var(--gray-200,#E2E8F0);
      background:var(--blue-pale,#F0F6FF);color:var(--blue-primary,#1A56A0);font-weight:600;cursor:pointer}
    .pc-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:18px}
    .pc-btn{min-height:46px;padding:0 20px;border-radius:12px;font-size:15.5px;font-weight:700;cursor:pointer;
      display:inline-flex;align-items:center;gap:8px;border:2px solid transparent}
    .pc-cancel{background:transparent;color:var(--gray-800,#1E293B);border-color:var(--gray-400,#94A3B8)}
    .pc-ok{background:var(--blue-primary,#1A56A0);color:#fff}
    .pc-btn:focus-visible,.pc-show:focus-visible{outline:3px solid #F59E0B;outline-offset:2px}
    .pc-banner{display:flex;gap:12px;align-items:flex-start;padding:14px 18px;margin:0 0 18px;border-radius:12px;
      font-size:15px;line-height:1.5;border:2px solid rgba(220,38,38,.45);background:rgba(220,38,38,.08);
      color:var(--gray-800,#1E293B)}
    .pc-banner svg{color:#DC2626;flex-shrink:0;margin-top:1px}
    .pc-banner button{margin-left:auto;background:none;border:0;font-size:20px;line-height:1;cursor:pointer;color:inherit}
  `;
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  const lockIcon = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>';

  // ── The passcode window ──
  const overlay = document.createElement('div');
  overlay.className = 'pc-overlay';
  overlay.hidden = true;
  overlay.innerHTML = `
    <div class="pc-box" role="dialog" aria-modal="true" aria-labelledby="pcTitle">
      <div class="pc-head"><div class="pc-icon">${lockIcon}</div><div class="pc-title" id="pcTitle">Office passcode</div></div>
      <p class="pc-text" id="pcText">Publishing shows this forecast to residents on the Community page. Enter the passcode kept in the health office.</p>
      <label class="pc-label" for="pcInput">Passcode</label>
      <div class="pc-row">
        <input class="pc-input" id="pcInput" type="password" autocomplete="off" maxlength="20" spellcheck="false">
        <button type="button" class="pc-show" id="pcShow">Show</button>
      </div>
      <div class="pc-actions">
        <button type="button" class="pc-btn pc-cancel" id="pcCancel">Cancel</button>
        <button type="button" class="pc-btn pc-ok" id="pcOk">${lockIcon.replace('22', '17').replace('22', '17')} Publish</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  const input = overlay.querySelector('#pcInput');
  let pending = null;

  function open(form) {
    pending = form;
    input.value = '';
    input.type = 'password';
    overlay.querySelector('#pcShow').textContent = 'Show';
    overlay.querySelector('#pcText').textContent = form.dataset.passcode ||
      'Publishing shows this forecast to residents on the Community page. Enter the passcode kept in the health office.';
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
    input.focus();
  }
  function close() {
    overlay.hidden = true;
    document.body.style.overflow = '';
    pending = null;
  }
  function send() {
    if (!pending || !input.value.trim()) { input.focus(); return; }
    let field = pending.querySelector('input[name="passcode"]');
    if (!field) {
      field = document.createElement('input');
      field.type = 'hidden';
      field.name = 'passcode';
      pending.appendChild(field);
    }
    field.value = input.value;
    const form = pending;
    close();
    form.submit();             // submit() skips the submit event, so the window doesn't open again
  }

  overlay.querySelector('#pcCancel').addEventListener('click', close);
  overlay.querySelector('#pcOk').addEventListener('click', send);
  overlay.querySelector('#pcShow').addEventListener('click', function () {
    input.type = input.type === 'password' ? 'text' : 'password';
    this.textContent = input.type === 'password' ? 'Show' : 'Hide';
  });
  input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); send(); } });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !overlay.hidden) close(); });
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });

  // Forms marked data-passcode open the window instead of submitting straight away
  document.addEventListener('submit', e => {
    const form = e.target;
    if (!form.matches('form[data-passcode]') || e.defaultPrevented) return;
    e.preventDefault();
    open(form);
  });

  // ── Message after a refused passcode (?passcode=wrong&n=3 etc.) ──
  const params = new URLSearchParams(location.search);
  const reason = params.get('passcode');
  if (reason) {
    const n = parseInt(params.get('n') || '0', 10);
    const text = {
      wrong:  `<strong>Wrong passcode. Nothing was published.</strong> ${n} tr${n === 1 ? 'y' : 'ies'} left before publishing is paused.`,
      locked: `<strong>Publishing is paused for ${n} minute${n === 1 ? '' : 's'}.</strong> Too many wrong passcodes. Nothing was published.`,
      empty:  '<strong>Nothing was published.</strong> Please enter the office passcode.',
      unset:  '<strong>Nothing was published.</strong> No office passcode has been set yet. Ask the IT Admin to set one on the Admin page.',
    }[reason];
    if (text) {
      const banner = document.createElement('div');
      banner.className = 'pc-banner';
      banner.setAttribute('role', 'alert');
      banner.innerHTML = `${lockIcon}<div>${text}</div><button type="button" aria-label="Close">×</button>`;
      banner.querySelector('button').addEventListener('click', () => banner.remove());
      const main = document.querySelector('.main-content');
      if (main) main.prepend(banner);
    }
    params.delete('passcode');
    params.delete('n');
    const rest = params.toString();
    history.replaceState(null, '', location.pathname + (rest ? '?' + rest : '') + location.hash);
  }
})();
