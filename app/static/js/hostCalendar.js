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

  // Shared display formatter: "07-Sep-2026". Only ever used for what
  // the host actually SEES -- never touches selectedStart/selectedEnd
  // themselves, which stay as FullCalendar's own raw values and get
  // sent to the backend unchanged. That raw, exclusive-end convention
  // must be preserved exactly as-is, since app/helpers/is_avail.py's
  // own overlap check (RoomBlock.end_date > arrival) depends on it --
  // changing what gets STORED would silently let a guest book the
  // final day of a host's intended block.
  const MONTH_ABBR = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];

  function formatDateDMY(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = MONTH_ABBR[date.getMonth()];
    const year = date.getFullYear();
    return `${day}-${month}-${year}`;
  }

  // Parses a plain "YYYY-MM-DD" string using numeric constructor args
  // (always local time) rather than new Date(string), which parses as
  // UTC midnight and can silently roll back a day once displayed,
  // depending on the browser's own local timezone.
  function parseDateOnly(isoDateStr) {
    const [year, month, day] = isoDateStr.split('-').map(Number);
    return new Date(year, month - 1, day);
  }

  const blockModal = new bootstrap.Modal(document.getElementById('blockModal'));

  const createBlockModal = new bootstrap.Modal(
    document.getElementById('createBlockModal'),
  );

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',

    selectable: true,

    editable: false,

    height: 'auto',

    headerToolbar: { left: 'prev,next today', center: 'title', right: '' },

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

      // Display-only: FullCalendar's own endStr is exclusive (the day
      // AFTER the last cell the host actually dragged over), so
      // selecting 7th-to-9th reports endStr as the 10th. Subtracting
      // a day here purely for what's shown to the host -- the real
      // selectedEnd sent to the backend on save stays exactly as
      // FullCalendar reported it, unchanged.
      const displayEnd = parseDateOnly(info.endStr);
      displayEnd.setDate(displayEnd.getDate() - 1);

      document.getElementById('selectedDates').textContent =
        `From ${formatDateDMY(parseDateOnly(info.startStr))} To ${formatDateDMY(displayEnd)}`;

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

      document.getElementById('blockStart').textContent = formatDateDMY(
        info.event.start,
      );

      if (info.event.end) {
        let end = new Date(info.event.end);

        end.setDate(end.getDate() - 1);

        document.getElementById('blockEnd').textContent = formatDateDMY(end);
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

        headers: { 'X-CSRFToken': csrfToken },
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
