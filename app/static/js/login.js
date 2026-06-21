// ── DengueTect Login Page JS ──

// Role card selection
function selectRole(selectedId) {
  document.querySelectorAll('.role-card').forEach(card => {
    card.classList.remove('selected');
  });
  document.getElementById(selectedId).classList.add('selected');
}

// Attach role card listeners
document.querySelectorAll('.role-card').forEach(card => {
  card.addEventListener('click', () => selectRole(card.id));
});

// Password toggle (bug: icon doesn't reset on re-hide)
const pwToggle = document.getElementById('pwToggle');
const pwInput  = document.getElementById('password');
const eyeIcon  = document.getElementById('eyeIcon');

pwToggle.addEventListener('click', () => {
  const show = pwInput.type === 'password';
  pwInput.type = show ? 'text' : 'password';
  eyeIcon.innerHTML = show
    ? `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8
       a18.45 18.45 0 0 1 5.06-5.94"/>
       <line x1="1" y1="1" x2="23" y2="23"/>`
    : `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
       <circle cx="12" cy="12" r="3"/>`;
});

// Form validation
document.getElementById('loginForm').addEventListener('submit', function(e) {
  e.preventDefault();
  let valid = true;

  const email    = document.getElementById('email');
  const pw       = document.getElementById('password');
  const emailErr = document.getElementById('email-err');
  const pwErr    = document.getElementById('pw-err');

  // reset errors
  [email, pw].forEach(el => el.classList.remove('error'));
  [emailErr, pwErr].forEach(el => el.style.display = 'none');

  // validate email
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRe.test(email.value.trim())) {
    email.classList.add('error');
    emailErr.style.display = 'block';
    valid = false;
  }

  // validate password
  if (!pw.value.trim()) {
    pw.classList.add('error');
    pwErr.style.display = 'block';
    valid = false;
  }

  if (valid) {
    this.submit();
  }
});