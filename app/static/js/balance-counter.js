document.addEventListener('DOMContentLoaded', function () {
  const balance = document.getElementById('hostBalance');

  if (!balance) {
    return;
  }

  const target = parseFloat(balance.innerText.replace(',', ''));

  let current = 0;

  const increment = target / 60;

  const timer = setInterval(function () {
    current += increment;

    if (current >= target) {
      current = target;

      clearInterval(timer);
    }

    balance.innerText = current.toLocaleString('en-GB', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }, 20);
});
