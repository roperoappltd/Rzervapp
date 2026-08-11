document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');
  const calendarUrl = calendarEl.dataset.calendarUrl;
  const blockUrl = calendarEl.dataset.blockUrl;

  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute('content');

  let selectedBlockId = null;
  let selectedStart = null;
  let selectedEnd = null;

  const blockModalEl = document.getElementById('blockModal');
  const blockModal = new bootstrap.Modal(blockModalEl);
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
        info.el.style.borderColor = '#ff385c';
        info.el.style.color = '#fff';
      }

      if (type === 'block') {
        info.el.style.backgroundColor = '#212529';
        info.el.style.borderColor = '#212529';
        info.el.style.color = '#fff';
      }

      info.el.style.borderRadius = '6px';
    },

    // CREATE BLOCK
    select: function (info) {
      selectedStart = info.startStr;
      selectedEnd = info.endStr;

      // format date options
      const dateOptions = {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      };

      const startDate = new Date(info.start);
      const endDate = new Date(info.end);

      // FullCalendar end date is exclusive
      endDate.setDate(endDate.getDate() - 1);

      const formattedStart = startDate.toLocaleDateString('en-GB', dateOptions);
      const formattedEnd = endDate.toLocaleDateString('en-GB', dateOptions);

      document.getElementById('selectedDates').textContent =
        `From ${formattedStart} → To ${formattedEnd}`;

      document.getElementById('blockReason').value = 'Maintenance';
      document.getElementById('blockNotes').value = '';

      createBlockModal.show();
    },

    // CLICK BLOCK EVENT
    eventClick: function (info) {
      const type = info.event.extendedProps.type;
      const dateOptions = {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      };

      if (type !== 'block') {
        return;
      }

      selectedBlockId = info.event.id;

      document.getElementById('blockReason').textContent =
        info.event.extendedProps.reason || info.event.title;
      document.getElementById('blockStart').textContent =
        info.event.start.toLocaleDateString('en-GB', dateOptions);

      if (info.event.end) {
        const actualEnd = new Date(info.event.end);

        actualEnd.setDate(actualEnd.getDate() - 1);

        document.getElementById('blockEnd').textContent =
          actualEnd.toLocaleDateString('en-GB', dateOptions);
      } else {
        document.getElementById('blockEnd').textContent = '';
      }
      blockModal.show();
    },
  });

  calendar.render();

  // REMOVE BLOCK
  document
    .getElementById('deleteBlockBtn')
    .addEventListener('click', function () {
      if (!selectedBlockId) {
        return;
      }

      fetch(`/api/room/{{ room.id }}/block/${selectedBlockId}`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': csrfToken,
        },
      })
        .then((res) => {
          if (!res.ok) {
            throw new Error(res.status);
          }
          return res.json();
        })
        .then((data) => {
          blockModal.hide();
          calendar.refetchEvents();
          alert(data.message);
        })
        .catch((error) => {
          console.error(error);
          alert('Unable to remove blocked dates.');
        });
    });
  // SAVE BLOCK
  document
    .getElementById('saveBlockBtn')
    .addEventListener('click', function () {
      const reason = document.getElementById('blockReasonSelect').value;

      const notes = document.getElementById('blockNotes').value;

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
        .then((res) => {
          if (!res.ok) {
            throw new Error(res.status);
          }

          return res.json();
        })
        .then((data) => {
          createBlockModal.hide();
          calendar.refetchEvents();
          calendar.unselect();
        })
        .catch((error) => {
          console.error(error);
          alert('Unable to save blocked dates.');
        });
    });
});
