document.addEventListener('DOMContentLoaded', function () {
  fetch('/host/earnings-chart')
    .then((response) => response.json())

    .then((data) => {
      const ctx = document.getElementById('earningsChart');

      if (!ctx) {
        return;
      }

      new Chart(ctx, {
        type: 'line',

        data: {
          labels: data.labels,

          datasets: [
            {
              label: 'Net Earnings (£)',
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
                  return ' £' + context.parsed.y.toFixed(2);
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
                  return '£' + value;
                },
              },
            },
          },
        },
      });
    });
});
