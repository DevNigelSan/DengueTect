// ── DengueTect Climate Input JS ──

// Clear all form fields
function clearForm() {
  document.querySelectorAll('input[type="number"]').forEach(input => {
    input.value = '';
  });
  document.getElementById('barangay').value = '';
  document.getElementById('week_date').value = '';
}

// Set default date to today
const dateInput = document.getElementById('week_date');
if (dateInput) {
  const today = new Date().toISOString().split('T')[0];
  dateInput.value = today;
}

// Validate all fields before submit
document.getElementById('submitBtn').addEventListener('click', function(e) {
  e.preventDefault();

  const barangay = document.getElementById('barangay').value;
  const weekDate = document.getElementById('week_date').value;
  const numbers  = document.querySelectorAll('input[type="number"]');

  let valid = true;

  if (!barangay) {
    alert('Please select a barangay.');
    valid = false;
  }

  if (!weekDate) {
    alert('Please select a week date.');
    valid = false;
  }

  numbers.forEach(input => {
    if (input.value === '' || isNaN(input.value)) {
      input.style.borderColor = '#DC2626';
      valid = false;
    } else {
      input.style.borderColor = '';
    }
  });

  if (!valid) return;

  // TODO: submit to Flask route
  document.querySelector('form') &&
    document.querySelector('form').submit();
});

// Clear red border on input focus
document.querySelectorAll('input[type="number"]').forEach(input => {
  input.addEventListener('focus', () => {
    input.style.borderColor = '';
  });
}); 