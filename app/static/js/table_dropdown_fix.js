// Fixes a documented Bootstrap limitation: a dropdown menu opening
// inside a .table-responsive wrapper can trigger unwanted horizontal
// and vertical scrollbars. Bootstrap's own docs explain why:
// "Responsive tables make use of overflow-y: hidden, which clips off
// any content that goes beyond the bottom or top edges of the table.
// In particular, this can clip off dropdown menus and other
// third-party widgets." When the dropdown expands, the browser
// recalculates the table wrapper's scrollable content area to include
// it, triggering scrollbars even though the menu was only ever meant
// to visually float on top.
//
// FIXED: an earlier version of this file used Popper's "fixed"
// positioning strategy to solve this -- but position: fixed is only
// viewport-relative if NO ancestor element has a CSS transform applied.
// This app uses AOS (Animate On Scroll, the data-aos="..." attributes
// throughout every template), which applies transforms during its
// animations -- causing the dropdown to position itself relative to
// that transformed ancestor instead of the viewport, landing in a
// seemingly random corner of the page.
//
// This version takes a different approach that never touches how the
// dropdown positions itself at all: it just temporarily disables the
// table wrapper's overflow/clipping WHILE a dropdown inside it is open
// (using Bootstrap's own show/hidden events, which bubble up to the
// wrapper), then restores it once the dropdown closes. No scrollbar
// side effect, dropdown stays exactly where Popper's normal default
// positioning already correctly puts it, and the table keeps its usual
// horizontal-scroll behavior on small screens the rest of the time.

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.table-responsive').forEach(function (wrapper) {
    wrapper.addEventListener('show.bs.dropdown', function () {
      wrapper.style.overflow = 'visible';
    });
    wrapper.addEventListener('hidden.bs.dropdown', function () {
      wrapper.style.overflow = 'auto';
    });
  });
});
