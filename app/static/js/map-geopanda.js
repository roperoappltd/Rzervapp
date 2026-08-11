// ======================================================
// ROOM GEO MAP
// Displays all available rooms on the booking homepage
// ======================================================

// Wait until page is fully loaded

document.addEventListener('DOMContentLoaded', function () {
  // ==================================================
  // CHECK MAP CONTAINER EXISTS
  // ==================================================

  const mapContainer = document.getElementById('roomMap');

  if (!mapContainer) {
    console.log('Room map container not found');

    return;
  }

  // ==================================================
  // CREATE MAP
  // ==================================================

  const map = L.map('roomMap', {
    zoomControl: true,

    scrollWheelZoom: false,
  });

  // Default location (Europe)

  map.setView([51.5074, -0.1278], 5);

  // ==================================================
  // MAP TILE
  // OpenStreetMap layer
  // ==================================================

  L.tileLayer(
    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',

    {
      attribution: '&copy; OpenStreetMap contributors',
    },
  ).addTo(map);

  // ==================================================
  // CUSTOM ROOM ICON
  // ==================================================

  const roomIcon = L.divIcon({
    className: 'room-marker',

    html: `

        <div class="room-marker-pin">
            <i class="bi bi-house-heart-fill"></i>

        </div>

        `,

    iconSize: [40, 40],
    iconAnchor: [20, 40],
  });

  // ==================================================
  // LOAD ROOMS FROM FLASK API
  // ==================================================

  fetch('/api/map/rooms')
    .then(function (response) {
      if (!response.ok) {
        throw new Error('Unable to load room locations');
      }

      return response.json();
    })

    .then(function (data) {
      // Store markers for automatic zoom

      const markers = [];

      // ==================================================
      // LOOP THROUGH ROOMS
      // ==================================================

      data.features.forEach(function (feature) {
        const room = feature.properties;

        const coordinates = feature.geometry.coordinates;

        // GeoJSON format:
        // longitude first
        // latitude second

        const latitude = coordinates[1];

        const longitude = coordinates[0];

        // ==================================================
        // CREATE MARKER
        // ==================================================

        const marker = L.marker(
          [latitude, longitude],

          {
            icon: roomIcon,
          },
        ).addTo(map);

        markers.push(marker);

        // ==================================================
        // POPUP CONTENT
        // ==================================================

        const popup = `

            <div class="room-popup">

                <img
                src="static/userpics/roompics/${room.image}"

                class="img-fluid rounded mb-2"
                style="
                width:220px;
                height:130px;
                object-fit:cover;
                "
                onerror="this.src='/static/images/no-image1.jpg'"
                >

                <h6 class="fw-bold">
                    ${room.name}
                </h6>

                <p class="mb-1">
                    <i class="bi bi-geo-alt"></i>
                    ${room.city}
                </p>

                <h6 class="text-danger">
                    £${room.price}
                    / night
                </h6>

                <a
                href="${room.url}"
                class="btn btn-sm btn-danger text-white w-100"
                >
                    View Room
                </a>

            </div>

            `;

        marker.bindPopup(popup);
      });

      // ==================================================
      // AUTO ZOOM TO SHOW ALL ROOMS
      // ==================================================

      if (markers.length > 0) {
        const group = L.featureGroup(markers);

        map.fitBounds(
          group.getBounds(),

          {
            padding: [40, 40],
          },
        );
      }
    })

    .catch(function (error) {
      console.error('Room map error:', error);
    });

  // ==================================================
  // RESPONSIVE MAP RESIZE
  // Important for Bootstrap columns
  // ==================================================

  window.addEventListener('resize', function () {
    setTimeout(
      function () {
        map.invalidateSize();
      },

      300,
    );
  });
});
