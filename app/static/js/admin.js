// ── DengueTect Admin Panel JS ──
// Add / Edit user window. Saving is done by the server; this only opens and fills the form.

const userModal = document.getElementById('userModal');
const userForm  = document.getElementById('userForm');

function openUserModal(btn, values) {
  const editing = !!(btn || (values && values.id));
  const v = values || (btn ? btn.dataset : {});

  document.getElementById('userModalTitle').textContent = editing ? 'Edit User' : 'Add User';
  document.getElementById('ufSave').textContent        = editing ? 'Save Changes' : 'Create Account';
  document.getElementById('ufPassLabel').textContent   = editing ? 'New password (optional)' : 'Password';
  document.getElementById('ufPassHint').textContent    = editing
    ? 'Leave blank to keep the current password. At least 8 characters if changed.'
    : 'At least 8 characters. Give it to the user privately.';

  userForm.action = editing
    ? userForm.dataset.editAction.replace('/0/', '/' + v.id + '/')
    : userForm.dataset.addAction;

  document.getElementById('ufName').value  = v.name  || '';
  document.getElementById('ufEmail').value = v.email || '';
  document.getElementById('ufRole').value  = v.role  || 'health_officer';
  const pass = document.getElementById('ufPass');
  pass.value    = '';
  pass.type     = 'password';
  pass.required = !editing;
  document.getElementById('ufShow').checked = false;

  // Error notices inside the window only apply to the form that was just sent back
  if (!values) document.querySelectorAll('.user-notice.in-modal').forEach(n => n.remove());

  userModal.hidden = false;
  document.body.style.overflow = 'hidden';
  document.getElementById('ufName').focus();
}

function closeUserModal() {
  userModal.hidden = true;
  document.body.style.overflow = '';
}

document.getElementById('ufShow').addEventListener('change', function () {
  document.getElementById('ufPass').type = this.checked ? 'text' : 'password';
});

// Close with Esc or by clicking outside the window
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !userModal.hidden) closeUserModal(); });
userModal.addEventListener('click', e => { if (e.target === userModal) closeUserModal(); });

// If the server sent the form back with an error, reopen it with what was typed
(function () {
  const d = userModal.dataset;
  if (!d.reopen) return;
  openUserModal(null, {
    id:    d.reopen === 'edit' ? d.uid : '',
    name:  d.name,
    email: d.email,
    role:  d.role,
  });
})();