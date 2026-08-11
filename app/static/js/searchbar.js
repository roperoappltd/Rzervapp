// document.addEventListener('DOMContentLoaded', function () {
//   const searchBtn = document.getElementById('searchToggle');
//   const searchPanel = document.getElementById('searchPanel');

//   searchBtn.addEventListener('click', function (e) {
//     e.preventDefault();
//     searchPanel.classList.toggle('show');
//   });

//   document.addEventListener('click', function (e) {
//     if (!searchPanel.contains(e.target) && !searchBtn.contains(e.target)) {
//       searchPanel.classList.remove('show');
//     }
//   });
// });

document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.getElementById('searchToggle');
  const panel = document.getElementById('searchPanel');

  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    panel.classList.toggle('show');
  });

  document.addEventListener('click', function (e) {
    if (!panel.contains(e.target) && !toggle.contains(e.target)) {
      panel.classList.remove('show');
    }
  });
});
