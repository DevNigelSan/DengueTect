// ── Delete Confirmation Modal ──
let pendingDeleteForm = null;

function showDeleteConfirm(event, btn) {
  event.preventDefault();
  pendingDeleteForm = btn.closest('form');
  document.getElementById('deleteOverlay').style.display = 'flex';

  document.getElementById('deleteConfirmBtn').onclick = function() {
    if (pendingDeleteForm) pendingDeleteForm.submit();
  };
}

function hideDeleteConfirm() {
  document.getElementById('deleteOverlay').style.display = 'none';
  pendingDeleteForm = null;
}

// Close on overlay click
document.addEventListener('click', function(e) {
  const overlay = document.getElementById('deleteOverlay');
  if (e.target === overlay) hideDeleteConfirm();
});