document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');

  if (!calendarEl) {
    console.error('Calendar element missing');
    return;
  }

  const calendarUrl = calendarEl.dataset.calendarUrl;

  const blockUrl = calendarEl.dataset.blockUrl;

  const roomId = calendarEl.dataset.roomId;

  console.log('Room ID:', roomId);

  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute('content');

  let selectedBlockId = null;

  let selectedStart = null;

  let selectedEnd = null;

  const blockModal = new bootstrap.Modal(document.getElementById('blockModal'));

  const createBlockModal = new bootstrap.Modal(
    document.getElementById('createBlockModal'),
  );

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',

    selectable: true,

    editable: false,

    height: 'auto',

    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: '',
    },

    events: calendarUrl,

    eventDidMount: function (info) {
      const type = info.event.extendedProps.type;

      if (type === 'booking') {
        info.el.style.backgroundColor = '#ff385c';
      }

      if (type === 'block') {
        info.el.style.backgroundColor = '#212529';
      }

      info.el.style.borderRadius = '6px';
    },

    // ==========================
    // CREATE BLOCK
    // ==========================

    select: function (info) {
      selectedStart = info.startStr;

      selectedEnd = info.endStr;

      document.getElementById('selectedDates').textContent =
        `From ${info.startStr} To ${info.endStr}`;

      createBlockModal.show();
    },

    // ==========================
    // CLICK EXISTING BLOCK
    // ==========================

    eventClick: function (info) {
      if (info.event.extendedProps.type !== 'block') {
        return;
      }

      selectedBlockId = info.event.id;

      console.log('Selected block:', selectedBlockId);

      document.getElementById('blockReason').textContent =
        info.event.extendedProps.reason;

      document.getElementById('blockStart').textContent =
        info.event.start.toLocaleDateString();

      if (info.event.end) {
        let end = new Date(info.event.end);

        end.setDate(end.getDate() - 1);

        document.getElementById('blockEnd').textContent =
          end.toLocaleDateString();
      }

      blockModal.show();
    },
  });

  calendar.render();

  // ==========================
  // DELETE BLOCK
  // ==========================

  document
    .getElementById('deleteBlockBtn')
    .addEventListener('click', function () {
      if (!selectedBlockId) {
        console.error('No block selected');

        return;
      }

      fetch(`/api/room/${roomId}/block/${selectedBlockId}`, {
        method: 'DELETE',

        headers: {
          'X-CSRFToken': csrfToken,
        },
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(response.status);
          }

          return response.json();
        })

        .then((data) => {
          console.log(data.message);

          blockModal.hide();

          calendar.refetchEvents();
        })

        .catch((error) => {
          console.error('Delete error:', error);

          alert('Unable to remove blocked dates.');
        });
    });

  // ==========================================
  // SAVE NEW BLOCK
  // ==========================================
  document
    .getElementById('saveBlockBtn')
    .addEventListener('click', function () {
      const reason = document.getElementById('blockReasonSelect').value;
      const notes = document.getElementById('blockNotes').value;

      console.log('Saving block:', {
        start: selectedStart,
        end: selectedEnd,
        reason: reason,
        notes: notes,
        url: blockUrl,
      });

      fetch(blockUrl, {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },

        body: JSON.stringify({
          start: selectedStart,
          end: selectedEnd,
          reason: reason,
          notes: notes,
        }),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error('HTTP error ' + response.status);
          }

          return response.json();
        })

        .then((data) => {
          console.log('Block created:', data);
          // Close modal

          createBlockModal.hide();
          // Remove calendar selection

          calendar.unselect();

          // Refresh calendar events
          calendar.refetchEvents();
        })

        .catch((error) => {
          console.error('Create block failed:', error);

          alert('Unable to block dates');
        });
    });
});
