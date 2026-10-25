// SECURITY: user-controlled text (usernames, room names) must be escaped
// before it goes into innerHTML, otherwise it runs as markup (stored XSS).
function escapeHtml(value) {
  return String(value == null ? '' : value).replace(/[&<>"'`]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '`': '&#96;' }[c];
  });
}

// Formats an amount in the host's own currency. Zero-decimal currencies
// (XOF, XAF...) are whole numbers grouped with a space and no comma
// ("1 250 000"); others keep two decimals with the usual comma grouping.
function formatMoney(amount, symbol, decimals) {
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

// ==========================================
// TOP 3 ROOMS REVENUE PIE CHART
// ==========================================

document.addEventListener('DOMContentLoaded', function () {
  const canvas = document.getElementById('topRoomsPieChart');

  // Stop if this page does not contain chart
  if (!canvas) {
    console.log('Top rooms chart not available');

    return;
  }

  fetch('/host/top-rooms-revenue')
    .then((response) => {
      if (!response.ok) {
        throw new Error('Server error: ' + response.status);
      }

      return response.json();
    })

    .then((data) => {
      console.log('Top room revenue:', data);

      // ================================
      // Prepare chart data
      // ================================

      const labels = data.map((room) => room.room);

      const values = data.map((room) => room.revenue);

      // ================================
      // Create Pie Chart
      // ================================

      new Chart(canvas.getContext('2d'), {
        type: 'pie',

        data: {
          labels: labels,

          datasets: [
            {
              data: values,

              backgroundColor: ['#F23679', '#57E5E0', '#5CFF7A'],

              borderWidth: 2,
            },
          ],
        },

        options: {
          responsive: true,

          maintainAspectRatio: false,

          plugins: {
            legend: {
              position: 'bottom',
            },

            tooltip: {
              callbacks: {
                label: function (context) {
                  const row = data[context.dataIndex] || {};
                  return (
                    context.label + ': ' +
                    formatMoney(context.parsed, row.symbol, row.decimals)
                  );
                },
              },
            },
          },
        },
      });

      // ================================
      // Populate Revenue Table
      // ================================

      const table = document.getElementById('topRoomsTable');

      if (table) {
        table.innerHTML = '';

        data.forEach((room) => {
          table.innerHTML += `

        <tr>

          <td>
          ${escapeHtml(room.room)}
          </td>

          <td class="text-center">
          ${room.booking_count}
          </td>

          <td class="text-end">
          ${escapeHtml(formatMoney(room.revenue, room.symbol, room.decimals))}
          </td>

          <td class="text-end">
          ${room.percentage}%
          </td>

        </tr>

          `;
        });
      }
    })

    .catch((error) => {
      console.error('Top room chart error:', error);
    });
});
