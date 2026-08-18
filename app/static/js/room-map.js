document.addEventListener('DOMContentLoaded', function () {
  const mapElement = document.getElementById('world_map');
  const roomDetailUrl = mapElement.dataset.roomUrl;

  if (!mapElement) {
    return;
  }

  fetch('/rooms/map-locations')
    .then((response) => response.json())

    .then((rooms) => {
      const markers = {};

      rooms.forEach(function (room, index) {
        markers[index] = {
          name: `${room.name}
                (${room.city})`,
          coords: [room.lat, room.lng],
          room: room,
        };
      });

      window.roomMap = new jsVectorMap({
        selector: '#world_map',
        map: 'world',
        backgroundColor: '#f8f9fa',
        zoomButtons: true,
        zoomOnScroll: false,

        regionStyle: {
          initial: { fill: '#e9ecef', stroke: '#ffffff', strokeWidth: 0.5 },

          hover: { fill: '#ffccd5' },
        },

        markers: markers,

        markerStyle: {
          initial: {
            fill: '#ff385c',
            stroke: '#ffffff',
            strokeWidth: 3,

            r: window.innerWidth < 576 ? 5 : 8,
          },

          hover: {
            fill: '#d81b45',

            r: 11,
          },
        },

        onMarkerClick: function (event, index) {
          showRoomCard(rooms[index]);
        },
      });
    })

    .catch((error) => {
      console.error('Room map error:', error);
    });
});

function showRoomCard(room) {
  const detailUrl = roomDetailUrl.replace('0', room.id);

  const popup = `

<div class="map-room-popup">

    <h6>
      ${room.name}
    </h6>

    <p>
      <i class="bi bi-geo-alt text-danger"></i>
      ${room.city}, ${room.country}
    </p>

    <p>
      <strong>
      ${room.price_display}
      </strong>
      per night
    </p>
    
    <div class="pt-2">
      <a
      href="${detailUrl}"
      class="btn btn-sm btn-success">

        View Room
      </a>
    </div> 
    
</div>

`;

  document.getElementById('mapTooltip').innerHTML = popup;
  document.getElementById('mapTooltip').style.display = 'block';
}
// resize observer
const mapContainer = document.getElementById('world_map');

if (mapContainer) {
  const resizeObserver = new ResizeObserver(() => {
    if (window.roomMap) {
      window.roomMap.updateSize();
    }
  });

  resizeObserver.observe(mapContainer);
}

window.addEventListener('resize', function () {
  if (window.roomMap) {
    window.roomMap.updateSize();
  }
});
