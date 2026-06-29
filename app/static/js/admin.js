// ── DengueTect Admin Panel JS ──

// Add user placeholder
function showAddUser() {
  alert('Add User form coming soon — will be implemented with Flask auth.');
}

// Deactivate user buttons
document.querySelectorAll('.btn-deactivate').forEach(btn => {
  btn.addEventListener('click', function() {
    const row  = this.closest('tr');
    const name = row.querySelector('.user-cell').textContent.trim();
    const confirmed = confirm(`Deactivate account for ${name}?`);
    if (!confirmed) return;

    const statusTag = row.querySelector('.status-tag');
    statusTag.textContent = 'Inactive';
    statusTag.className   = 'status-tag inactive';

    this.textContent  = 'Activate';
    this.className    = 'btn-activate';

    // re-attach activate listener
    this.addEventListener('click', activateHandler);
    this.removeEventListener('click', arguments.callee);
  });
});

// Activate user buttons
document.querySelectorAll('.btn-activate').forEach(btn => {
  btn.addEventListener('click', activateHandler);
});

function activateHandler() {
  const row  = this.closest('tr');
  const name = row.querySelector('.user-cell').textContent.trim();
  const confirmed = confirm(`Reactivate account for ${name}?`);
  if (!confirmed) return;

  const statusTag = row.querySelector('.status-tag');
  statusTag.textContent = 'Active';
  statusTag.className   = 'status-tag active';

  this.textContent = 'Deactivate';
  this.className   = 'btn-deactivate';
}