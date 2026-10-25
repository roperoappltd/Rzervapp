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

  // Currency symbol for THIS checkout's guest currency -- was hardcoded
  // as "£" before, which was wrong for any guest not paying in GBP.
  const metaEl = document.getElementById('checkoutMeta');
  const currencySymbol = metaEl ? metaEl.dataset.currencySymbol : '£';
  // 0 for currencies without cents (XOF...), otherwise 2
  const decimals = metaEl && metaEl.dataset.decimals === '0' ? 0 : 2;
  const symbolSpace = currencySymbol.length > 1 ? ' ' : '';

  function fmt(n) {
    return Number(n).toFixed(decimals);
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

    discountEl.innerText = fmt(discount);
    finalEl.innerText = fmt(finalTotal);
    subtotalEl.innerText = fmt(subtotal);
    submitBtn.value = `Pay now ${currencySymbol}${symbolSpace}${fmt(finalTotal)}`;
  }

  input.addEventListener('input', function () {
    clearTimeout(debounceTimer);

    debounceTimer = setTimeout(() => {
      const code = input.value.trim();
      const subtotal = Number(subtotalEl.dataset.value) || 0;

      // RESET STATE (empty or too short to be a code). The server is told
      // as well: it remembers an applied voucher in the session, and
      // without this the checkout would still charge the discount that
      // this page no longer shows.
      if (code.length < 5) {
        msg.innerHTML = '';
        updateUI(subtotal, 0);
        clearVoucherOnServer();
        return;
      }

      fetch('/check-voucher', {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken && { 'X-CSRFToken': csrfToken }),
        },

        credentials: 'same-origin',

        body: JSON.stringify({ voucher_code: code }),
      })
        .then((response) => {
          // 429 = too many attempts; the body still carries a message
          if (!response.ok && response.status !== 429) {
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

  function clearVoucherOnServer() {
    fetch('/check-voucher', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(csrfToken && { 'X-CSRFToken': csrfToken }),
      },
      credentials: 'same-origin',
      body: JSON.stringify({ voucher_code: '' }),
    }).catch((err) => console.error(err));
  }

  function updateUI(subtotal, discount) {
    const safeSubtotal = Number(subtotal) || 0;
    const safeDiscount = Number(discount) || 0;

    const finalTotal = Math.max(safeSubtotal - safeDiscount, 0);

    // update UI fields
    discountEl.innerText = fmt(safeDiscount);
    finalEl.innerText = fmt(finalTotal);

    // update button text
    submitBtn.value = `Pay ${currencySymbol}${symbolSpace}${fmt(finalTotal)}`;
  }
});
