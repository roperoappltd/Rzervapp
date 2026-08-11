 
<script>
(function(){
  // ---------- Rate Guest modal ----------
  const rateModal = document.getElementById('rateGuestModal');
  const starIcons = document.querySelectorAll('#rateGuestStars .bi');
  const rateInput = document.getElementById('rateGuestRateInput');
  const rateForm = document.getElementById('rateGuestForm');
  const rateSubtitle = document.getElementById('rateGuestSubtitle');
  const messageBox = document.getElementById('rateGuestMessage');
  const charCount = document.getElementById('rateGuestCharCount');
 
  function setStars(value){
    starIcons.forEach(icon => {
      const v = parseInt(icon.dataset.value, 10);
      icon.classList.toggle('bi-star-fill', v <= value);
      icon.classList.toggle('bi-star', v > value);
      icon.classList.toggle('jw-active', v <= value);
    });
    rateInput.value = value;
  }
 
  starIcons.forEach(icon => {
    icon.addEventListener('click', () => setStars(parseInt(icon.dataset.value, 10)));
  });
 
  messageBox.addEventListener('input', () => {
    charCount.textContent = messageBox.value.length;
  });
 
  rateModal.addEventListener('show.bs.modal', event => {
    const button = event.relatedTarget;
    const bookingId = button.dataset.bookingId;
    const guestName = button.dataset.guestName;
 
    rateForm.action = `/rate-guest/${bookingId}`;
    rateSubtitle.textContent = guestName ? `${guestName}` : '';
    setStars(0);
    messageBox.value = '';
    charCount.textContent = '0';
  });
 
  // ---------- View Guest Reviews modal ----------
  const reviewsModal = document.getElementById('guestReviewsModal');
  const reviewsSubtitle = document.getElementById('guestReviewsSubtitle');
  const reviewsBody = document.getElementById('guestReviewsBody');
 
  function starsHtml(rating){
    let html = '';
    for(let i = 1; i <= 5; i++){
      html += `<i class="bi ${i <= rating ? 'bi-star-fill' : 'bi-star'}"></i> `;
    }
    return html;
  }
 
  reviewsModal.addEventListener('show.bs.modal', event => {
    const button = event.relatedTarget;
    const guestId = button.dataset.guestId;
    const guestName = button.dataset.guestName;
 
    reviewsSubtitle.textContent = guestName || '';
    reviewsBody.innerHTML = `<div class="jw-loading">{{ _('Loading...') }}</div>`;
 
    fetch(`/api/guest-reviews/${guestId}`)
      .then(r => r.json())
      .then(reviews => {
        if(!reviews.length){
          reviewsBody.innerHTML = `
            <div class="jw-empty-state">
              <i class="bi bi-chat-square-heart"></i>
              {{ _('No reviews yet for this guest.') }}
            </div>`;
          return;
        }
 
        reviewsBody.innerHTML = reviews.map(r => `
          <div class="jw-review-card">
            <div class="jw-review-stars">${starsHtml(r.rate_us)}</div>
            <div>${r.message}</div>
            <div class="jw-review-meta">${r.host} &middot; ${r.date_posted}</div>
          </div>
        `).join('');
      })
      .catch(() => {
        reviewsBody.innerHTML = `<div class="jw-empty-state">{{ _('Could not load reviews right now.') }}</div>`;
      });
  });
})();
</script>