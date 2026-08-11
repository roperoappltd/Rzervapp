document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('voucher_code');
  const msg = document.getElementById('msg');

  const subtotalEl = document.getElementById('subtotal');
  const discountEl = document.getElementById('discount');
  const finalEl = document.getElementById('final-total');
  const submitBtn = document.getElementById('submit-btn');

  // safety check
  if (!input || !msg || !subtotalEl || !discountEl || !finalEl || !submitBtn) {
    console.error('Missing required DOM elements');
    return;
  }

  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : null;

  let debounceTimer;

  // 🔥 INIT BUTTON (IMPORTANT FIX)
  initUI();

  function initUI() {
    const subtotal = Number(subtotalEl.dataset.value) || 0;
    const discount = Number(discountEl.dataset.value) || 0;
    const finalTotal = Number(finalEl.dataset.value) || 0;

    discountEl.innerText = discount.toFixed(2);
    finalEl.innerText = finalTotal.toFixed(2);
    submitBtn.value = `Pay now £${finalTotal.toFixed(2)}`;
  }

  input.addEventListener('input', function () {
    clearTimeout(debounceTimer);

    debounceTimer = setTimeout(() => {
      const code = input.value.trim();
      const subtotal = Number(subtotalEl.dataset.value) || 0;

      // RESET STATE (empty input)
      if (!code) {
        msg.innerHTML = '';
        updateUI(subtotal, 0);
        return;
      }

      // skip short input
      if (code.length < 5) {
        msg.innerHTML = '';
        updateUI(subtotal, 0);
        return;
      }

      fetch('/check-voucher', {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken && { 'X-CSRFToken': csrfToken }),
        },

        credentials: 'same-origin',

        body: JSON.stringify({
          voucher_code: code,
        }),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error('Server error');
          }
          return response.json();
        })

        .then((data) => {
          const discount = Number(data.discount) || 0;

          msg.innerHTML = data.message || '';

          updateUI(subtotal, discount);
        })

        .catch((err) => {
          console.error(err);

          msg.innerHTML =
            "<span style='color:red'>Server error... try refresh page</span>";
        });
    }, 400);
  });

  function updateUI(subtotal, discount) {
    const safeSubtotal = Number(subtotal) || 0;
    const safeDiscount = Number(discount) || 0;

    const finalTotal = Math.max(safeSubtotal - safeDiscount, 0);

    // update UI fields
    discountEl.innerText = safeDiscount.toFixed(2);
    finalEl.innerText = finalTotal.toFixed(2);

    // update button text
    submitBtn.value = `Pay £${finalTotal.toFixed(2)}`;
  }
});
