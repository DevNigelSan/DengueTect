// ── DengueTect History Page JS ──

function filterHistory() {
  const brgy    = document.getElementById('filter-brgy').value;
  const risk    = document.getElementById('filter-risk').value;
  const rows    = document.querySelectorAll('#historyBody tr[data-brgy]');

  let visible = 0;

  rows.forEach(row => {
    const brgyMatch = brgy === 'all' || row.dataset.brgy === brgy;
    const riskMatch = risk === 'all' || row.dataset.risk === risk;

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
  filterHistory();
}