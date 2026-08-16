// Generic "are you sure?" confirmation for destructive form submissions.
// Opt in on any <form> with class="confirm-before-submit" and a
// data-confirm-message="..." attribute holding the (translated) prompt
// text. Deliberately reads the message from a data attribute rather
// than an inline onsubmit="confirm('...')" handler -- a translated
// string embedded directly in a JS string literal risks breaking if it
// ever contains an apostrophe (common in French), since that would
// prematurely close the JS string. HTML attributes don't have that
// problem.

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.confirm-before-submit').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      const message = form.dataset.confirmMessage || 'Are you sure?';
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
});
