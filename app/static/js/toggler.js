document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.getElementById('pillToggle');
  const menu = document.getElementById('pillMenu');

  // open / close
  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    menu.classList.toggle('show');
  });

  // close when clicking outside
  document.addEventListener('click', function (e) {
    if (!menu.contains(e.target) && !toggle.contains(e.target)) {
      menu.classList.remove('show');
    }
  });

  // close on link click (important UX improvement)
  menu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      menu.classList.remove('show');
    });
  });
});
