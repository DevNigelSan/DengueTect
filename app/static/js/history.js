// ── DengueTect History Page JS ──

function filterHistory() {
  const brgy    = document.getElementById('filter-brgy').value;
  const risk    = document.getElementById('filter-risk').value;
  const rows    = document.querySelectorAll('#historyBody tr');

  let visible = 0;

  rows.forEach(row => {
    const rowBrgy = row.dataset.brgy;
    const rowRisk = row.dataset.risk;

    const brgyMatch = brgy === 'all' || rowBrgy === brgy;
    const riskMatch = risk === 'all' || rowRisk === risk;

    if (brgyMatch && riskMatch) {
      row.classList.remove('hidden');
      visible++;
    } else {
      row.classList.add('hidden');
    }
  });

  document.getElementById('recordCount').textContent =
    `Showing ${visible} record${visible !== 1 ? 's' : ''}`;
}

function clearFilters() {
  document.getElementById('filter-brgy').value = 'all';
  document.getElementById('filter-risk').value = 'all';
  document.getElementById('filter-from').value = '';
  document.getElementById('filter-to').value   = '';
  filterHistory();
}

// set default date range to last 30 days
window.addEventListener('load', () => {
  const to   = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 30);

  document.getElementById('filter-to').value   = to.toISOString().split('T')[0];
  document.getElementById('filter-from').value = from.toISOString().split('T')[0];
});