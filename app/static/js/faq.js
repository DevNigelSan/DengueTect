// ── DengueTect Help Center (FAQ) ──

(function () {
  const searchBox   = document.querySelector('.faq-search');
  const searchInput = document.getElementById('faqSearch');
  const clearBtn    = document.getElementById('faqSearchClear');
  const resultText  = document.getElementById('faqResultText');
  const emptyState  = document.getElementById('faqEmpty');
  const emptyTerm   = document.getElementById('faqEmptyTerm');
  const sections    = Array.from(document.querySelectorAll('.faq-cat'));
  const items       = Array.from(document.querySelectorAll('.faq-item'));
  const terms       = Array.from(document.querySelectorAll('.faq-term'));
  const navLinks    = Array.from(document.querySelectorAll('.faq-nav-link'));
  const TOTAL       = items.length + terms.length;

  // Remember the original HTML so search highlights can be undone cleanly
  const searchable = [...items, ...terms];
  searchable.forEach(el => { el.dataset.original = el.innerHTML; });

  // ── ACCORDION ──
  function setOpen(item, open) {
    item.classList.toggle('open', open);
    const btn = item.querySelector('.faq-q');
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.faq-q');
    if (!btn) return;
    const item = btn.closest('.faq-item');
    setOpen(item, !item.classList.contains('open'));
  });

  document.getElementById('faqExpandAll').addEventListener('click', () => {
    items.filter(i => !i.hidden).forEach(i => setOpen(i, true));
  });

  document.getElementById('faqCollapseAll').addEventListener('click', () => {
    items.forEach(i => setOpen(i, false));
  });

  // ── JUMP TO A QUESTION OR TOPIC ──
  function goTo(id, flash = true) {
    const target = document.getElementById(id);
    if (!target) return;

    if (target.classList.contains('faq-item')) {
      if (target.hidden) clearSearch();
      setOpen(target, true);
    }

    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    history.replaceState(null, '', '#' + id);

    if (flash && target.classList.contains('faq-item')) {
      target.classList.remove('flash');
      void target.offsetWidth; // restart animation
      target.classList.add('flash');
    }
  }

  document.querySelectorAll('[data-goto]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      goTo(el.dataset.goto);
    });
  });

  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      goTo(link.dataset.cat, false);
    });
  });

  // ── SEARCH ──
  function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function highlight(root, regex) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: n => n.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach(node => {
      const text = node.nodeValue;
      regex.lastIndex = 0;
      if (!regex.test(text)) return;
      regex.lastIndex = 0;

      const frag = document.createDocumentFragment();
      let last = 0;
      text.replace(regex, (match, offset) => {
        frag.appendChild(document.createTextNode(text.slice(last, offset)));
        const mark = document.createElement('mark');
        mark.textContent = match;
        frag.appendChild(mark);
        last = offset + match.length;
      });
      frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  function updateCounts() {
    sections.forEach(sec => {
      const visible = sec.querySelectorAll('.faq-item:not([hidden]), .faq-term:not([hidden])').length;
      sec.hidden = visible === 0;
      const badge = document.querySelector(`[data-count-for="${sec.id}"]`);
      if (badge) badge.textContent = visible;
      const link = document.querySelector(`.faq-nav-link[data-cat="${sec.id}"]`);
      if (link) link.classList.toggle('is-empty', visible === 0);
    });
  }

  function runSearch() {
    const raw   = searchInput.value.trim();
    const query = raw.toLowerCase();
    searchBox.classList.toggle('has-value', raw.length > 0);

    // restore original content
    searchable.forEach(el => {
      const wasOpen = el.classList.contains('open');
      el.innerHTML = el.dataset.original;
      if (el.classList.contains('faq-item')) setOpen(el, wasOpen);
      el.hidden = false;
    });

    if (!query) {
      emptyState.hidden = true;
      resultText.innerHTML = `Browse all <strong>${TOTAL}</strong> answers and terms`;
      updateCounts();
      return;
    }

    const words = query.split(/\s+/).filter(Boolean);
    const regex = new RegExp(words.map(escapeRegex).join('|'), 'gi');
    let matches = 0;
    let firstMatch = null;

    searchable.forEach(el => {
      const text = el.textContent.toLowerCase();
      const hit  = words.every(w => text.includes(w));
      el.hidden  = !hit;
      if (hit) {
        matches++;
        highlight(el, regex);
        if (!firstMatch && el.classList.contains('faq-item')) firstMatch = el;
      }
    });

    // open the best match so the answer is visible right away
    items.forEach(i => { if (!i.hidden) setOpen(i, false); });
    if (firstMatch) setOpen(firstMatch, true);

    updateCounts();
    updateActive();
    emptyState.hidden = matches > 0;
    emptyTerm.textContent = raw;
    const safe = raw.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    resultText.innerHTML = matches
      ? `<strong>${matches}</strong> result${matches !== 1 ? 's' : ''} for "<strong>${safe}</strong>"`
      : `No results for "<strong>${safe}</strong>"`;
  }

  let timer;
  searchInput.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(runSearch, 120);
  });

  function clearSearch() {
    searchInput.value = '';
    runSearch();
  }

  clearBtn.addEventListener('click', () => { clearSearch(); searchInput.focus(); });
  document.getElementById('faqEmptyClear').addEventListener('click', () => { clearSearch(); searchInput.focus(); });

  // "/" focuses search, Esc clears it
  document.addEventListener('keydown', (e) => {
    const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName);
    if (e.key === '/' && !typing) {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
    if (e.key === 'Escape' && document.activeElement === searchInput) {
      clearSearch();
      searchInput.blur();
    }
  });

  // ── HIGHLIGHT CURRENT TOPIC IN SIDEBAR ──
  function setActive(id) {
    navLinks.forEach(l => l.classList.toggle('active', l.dataset.cat === id));
  }

  // The active topic is the last visible section whose top has passed under the navbar
  function updateActive() {
    const shown = sections.filter(s => !s.hidden);
    if (!shown.length) return;
    let current = shown[0];
    shown.forEach(sec => {
      if (sec.getBoundingClientRect().top <= 160) current = sec;
    });
    const atBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 4;
    if (atBottom) current = shown[shown.length - 1];
    setActive(current.id);
  }

  let ticking = false;
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { updateActive(); ticking = false; });
  }, { passive: true });

  // ── INITIAL STATE ──
  runSearch();
  updateActive();

  // Open a question or topic from the link (e.g. /faq#q-fetch or /faq#running)
  if (location.hash) {
    const id = decodeURIComponent(location.hash.slice(1));
    setTimeout(() => goTo(id), 250);
  }

  // Also react when a link changes the #question while already on this page
  window.addEventListener('hashchange', () => {
    goTo(decodeURIComponent(location.hash.slice(1)));
  });
})();