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
                  return (
                    context.label + ': £' + context.parsed.toLocaleString()
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
          ${room.room}
          </td>

          <td class="text-center">
          ${room.booking_count}
          </td>

          <td class="text-end">
          £${room.revenue.toLocaleString()}
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
