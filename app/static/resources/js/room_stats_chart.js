/**
 * Renders and controls the room-views line chart on the room stats page.
 * Reads its data from the #rsChartData element's data-week/data-month
 * attributes (set server-side via Jinja's tojson filter) rather than a
 * window global -- keeps Jinja-rendered values out of the <script> tag
 * entirely, which also avoids editor JS-linters flagging Jinja syntax
 * as invalid JavaScript (it isn't real JS, it's substituted before the
 * browser ever sees it, but editors can't know that).
 */

document.addEventListener('DOMContentLoaded', function () {
  const dataEl = document.getElementById('rsChartData');
  const weekData = JSON.parse(dataEl.dataset.week);
  const monthData = JSON.parse(dataEl.dataset.month);

  const canvas = document.getElementById('roomViewsChart');
  const chartCard = document.getElementById('rsChartCard');
  const periodToggle = document.getElementById('rsPeriodToggle');
  const themeToggle = document.getElementById('rsThemeToggle');

  let currentPeriod = 'week';
  let isDark = false;

  // Brand coral, with a soft gradient fill under the line -- matches
  // the rest of Jambo's UI rather than Chart.js's default blue.
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 360);
  gradient.addColorStop(0, 'rgba(255, 56, 92, 0.25)');
  gradient.addColorStop(1, 'rgba(255, 56, 92, 0)');

  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: weekData.map(function (d) {
        return d.date;
      }),
      datasets: [
        {
          label: 'Views',
          data: weekData.map(function (d) {
            return d.count;
          }),
          borderColor: '#ff385c',
          backgroundColor: gradient,
          borderWidth: 2.5,
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: '#ff385c',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          fill: true,
          tension: 0.35,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        // Hover tooltip -- this is Chart.js's built-in behavior, just
        // styled to match the card rather than the library default.
        tooltip: {
          backgroundColor: '#1c1f26',
          titleColor: '#fff',
          bodyColor: '#fff',
          padding: 12,
          cornerRadius: 10,
          displayColors: false,
          callbacks: {
            label: function (context) {
              const count = context.parsed.y;
              return count + (count === 1 ? ' view' : ' views');
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#8a8a8a', maxRotation: 0 },
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#8a8a8a', precision: 0 },
          grid: { color: 'rgba(0,0,0,0.06)' },
        },
      },
    },
  });

  /**
   * Swaps the chart's data between the Week and Month datasets. Both
   * are already loaded client-side -- this never re-fetches anything.
   */
  function setPeriod(period) {
    currentPeriod = period;
    const data = period === 'month' ? monthData : weekData;

    chart.data.labels = data.map(function (d) {
      return d.date;
    });
    chart.data.datasets[0].data = data.map(function (d) {
      return d.count;
    });
    chart.update();

    periodToggle.querySelectorAll('.rs-seg-btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.period === period);
    });
  }

  periodToggle.querySelectorAll('.rs-seg-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      setPeriod(btn.dataset.period);
    });
  });

  /**
   * Toggles the card between light and dark backgrounds. CSS alone
   * handles the card's own colors (see .rs-dark in the template), but
   * Chart.js renders to a <canvas> -- it does NOT respond to CSS at
   * all, so the chart's own colors have to be updated here in JS too.
   */
  function setTheme(dark) {
    isDark = dark;
    chartCard.classList.toggle('rs-dark', dark);

    const gridColor = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
    const tickColor = dark ? '#c9c9c9' : '#8a8a8a';

    chart.options.scales.x.ticks.color = tickColor;
    chart.options.scales.y.ticks.color = tickColor;
    chart.options.scales.y.grid.color = gridColor;
    chart.update();

    themeToggle.innerHTML = dark
      ? '<i class="bi bi-sun"></i>'
      : '<i class="bi bi-moon-stars"></i>';
  }

  themeToggle.addEventListener('click', function () {
    setTheme(!isDark);
  });
});
