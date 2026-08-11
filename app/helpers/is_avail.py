from app.models.roommodel import RoomBlock
from app.models.bookmodel import Bookings


def is_available(room_id, arrival, departure):
    booking_overlap = Bookings.query.filter(
        Bookings.room_id == room_id,
        Bookings.status == "Confirmed",
        Bookings.arrival < departure,
        Bookings.departure > arrival
    ).first()

    block_overlap = RoomBlock.query.filter(
        RoomBlock.room_id == room_id,
        RoomBlock.start_date < departure,
        RoomBlock.end_date > arrival
    ).first()

    return not booking_overlap and not block_overlap
