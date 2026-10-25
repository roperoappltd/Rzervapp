// Amount in the host's own currency: whole numbers grouped with a space
// and no comma for zero-decimal currencies (XOF...), two decimals otherwise.
function chartMoney(amount, symbol, decimals) {
  const n = Number(amount) || 0;
  let text;
  if (decimals === 0) {
    text = Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '\u00A0');
  } else {
    text = n.toLocaleString('en-GB', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }
  const sym = symbol || '';
  return sym + (sym.length > 1 ? '\u00A0' : '') + text;
}

document.addEventListener('DOMContentLoaded', function () {
  fetch('/host/earnings-chart')
    .then((response) => response.json())

    .then((data) => {
      const ctx = document.getElementById('earningsChart');

      if (!ctx) {
        return;
      }

      const symbol = data.symbol || '£';
      const decimals = typeof data.decimals === 'number' ? data.decimals : 2;

      new Chart(ctx, {
        type: 'line',

        data: {
          labels: data.labels,

          datasets: [
            {
              label: 'Net Earnings (' + symbol + ')',
              data: data.values,
              borderColor: '#C755D8', // line colour
              backgroundColor: '#c755d828', // light fill under line
              pointBackgroundColor: '#C755D8',
              pointBorderColor: '#ffffff',
              pointRadius: 5,
              pointHoverRadius: 7,
              tension: 0.4,

              fill: true,
            },
          ],
        },

        options: {
          responsive: true,

          plugins: {
            legend: {
              display: true,
            },

            tooltip: {
              callbacks: {
                label: function (context) {
                  return ' ' + chartMoney(context.parsed.y, symbol, decimals);
                },
              },
            },
          },

          scales: {
            y: {
              beginAtZero: true,

              ticks: {
                //stepSize: 100, // Increase Y-axis by £200 increments//
                callback: function (value) {
                  return chartMoney(value, symbol, decimals);
                },
              },
            },
          },
        },
      });
    });
});
