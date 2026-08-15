// Generic password visibility toggle. Unlike script.js's
// TravelBookingLoginForm class (which is built specifically for the
// login page and hardcodes document.getElementById('loginForm')), this
// makes no assumptions about the surrounding form at all -- it just
// finds every .password-toggle button, locates the password input
// inside the same .form-group, and wires up a click handler. Safe to
// include on any page (register, reset password, etc.) regardless of
// what else is or isn't on that page.

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.password-toggle').forEach(function (toggleBtn) {
    const group = toggleBtn.closest('.form-group');
    const input = group
      ? group.querySelector('input[type="password"], input.password-field')
      : null;

    if (!input) {
      return; // nothing to toggle -- fail silently rather than throw
    }

    toggleBtn.addEventListener('click', function () {
      const isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';

      // FIXED: was toggleBtn.style.transform = 'scale(...)', which
      // completely replaced the CSS's translateY(-50%) vertical
      // centering, causing the icon to visibly jump out of position on
      // every click. Combining both transforms instead preserves the
      // centering while still animating the scale.
      const scale = isHidden ? 'scale(0.9)' : 'scale(1)';
      toggleBtn.style.transform = `translateY(-50%) ${scale}`;
      setTimeout(function () {
        toggleBtn.style.transform = 'translateY(-50%) scale(1)';
      }, 150);
    });
  });
});
