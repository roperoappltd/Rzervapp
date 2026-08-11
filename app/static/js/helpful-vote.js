/**
 * Handles the "Helpful" vote button on room reviews (roomdetails.html).
 *
 * Each button already renders server-side with its correct initial
 * state (active/inactive, current count) via Jinja, using the
 * my_helpful_votes set computed once in the roomdetail() route. This
 * script only handles what happens AFTER a click -- it never needs to
 * know the full list of reviews or votes, just react to one button at
 * a time.
 */

document.addEventListener('DOMContentLoaded', function () {
  // The CSRF token meta tag lives in base.html and is present on every
  // page, including this one -- read it once here rather than per click.
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = csrfMeta ? csrfMeta.content : '';

  // Grab every "Helpful" button currently on the page. This runs once,
  // after the DOM is fully loaded, so all review rows already exist.
  const helpfulButtons = document.querySelectorAll('.helpful-btn');

  helpfulButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      handleHelpfulClick(button);
    });
  });

  /**
   * Sends the vote toggle to the server and updates this one button's
   * appearance based on the response. Does not touch any other button
   * or reload the page.
   */
  function handleHelpfulClick(button) {
    // Disabled buttons belong to logged-out users or the review's own
    // author (rendered disabled server-side) -- ignore clicks on those.
    if (button.disabled) {
      return;
    }

    const reviewId = button.dataset.reviewId;

    fetch('/review/' + reviewId + '/helpful', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
    })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        // The server can reject the vote (e.g. self-vote caught server-
        // side too, as a second layer of defense beyond the disabled
        // attribute) -- in that case, just do nothing rather than show
        // a broken/incorrect state.
        if (data.error) {
          return;
        }

        updateButtonAppearance(button, data.voted, data.count);
      })
      .catch(function () {
        // Network failure or non-JSON response -- fail silently rather
        // than show the user a broken button state. The vote simply
        // didn't register; clicking again will retry.
      });
  }

  /**
   * Updates a single button's icon, active styling, and displayed count
   * to match the server's confirmed result. The server's response is
   * always the source of truth here -- this never guesses the new state
   * itself, it only reflects back what the server actually recorded.
   */
  function updateButtonAppearance(button, voted, count) {
    const icon = button.querySelector('.bi');
    const countLabel = button.querySelector('.helpful-count');

    button.classList.toggle('jw-active', voted);

    icon.className = voted
      ? 'bi bi-hand-thumbs-up-fill'
      : 'bi bi-hand-thumbs-up';

    countLabel.textContent = count;
  }
});
