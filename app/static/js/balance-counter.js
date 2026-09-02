document.addEventListener('DOMContentLoaded', function () {
  const balance = document.getElementById('hostBalance');

  if (!balance) {
    return;
  }

  const rawText = balance.innerText.trim();

  // FIXED: was .replace(',', '') -- only strips the FIRST comma, not
  // all of them. A large XOF balance like "1,234,567" would leave the
  // second comma in place, and parseFloat() stops at the first
  // non-numeric character it hits -- silently parsing this as just "1".
  const target = parseFloat(rawText.replace(/,/g, ''));

  // FIXED: was hardcoded to always show 2 decimal places, regardless
  // of currency. The server already correctly decides this (via
  // available_balance_number, which respects ZERO_DECIMAL_CURRENCIES)
  // -- detecting whether that server-rendered value already has a
  // decimal point, and preserving that same choice throughout the
  // animation, rather than overriding it with a fixed rule here.
  const hasDecimals = rawText.replace(/,/g, '').includes('.');

  let current = 0;

  const increment = target / 60;

  const timer = setInterval(function () {
    current += increment;

    if (current >= target) {
      current = target;

      clearInterval(timer);
    }

    balance.innerText = current.toLocaleString('en-GB', {
      minimumFractionDigits: hasDecimals ? 2 : 0,
      maximumFractionDigits: hasDecimals ? 2 : 0,
    });
  }, 20);
});
