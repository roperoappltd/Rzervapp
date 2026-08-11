from flask import url_for
from app.models.roommodel import Rooms
from datetime import datetime
from .is_avail import is_available

def build_room_query(location=None, room_category=None, min_price=None,
                      max_price=None, arrival=None, departure=None, guests=None):
    '''
    Shared query-building logic used by both the HTML roomsearch route and
    the AI agent's search_rooms tool. arrival/departure are expected as 
    "YYYY-MM-DD" strings (or None).Returns a dict:
      {"query": <SQLAlchemy query or None>, "error": <code or None>}
    error codes (map to the exact flash messages the original route used):
      "invalid_dates"            -> could not parse arrival/departure
      "departure_before_arrival" -> departure <= arrival
      "no_availability"          -> valid dates, but no rooms free for them
                                     (query is still returned, filtered to
                                     an empty set, so pagination keeps working
                                     for the HTML route)
      None                       -> success, query is usable as-is
    '''
    query = Rooms.query
 
    if location:
        query = query.filter(Rooms.room_location.ilike(f"%{location}%"))
    if room_category:
        query = query.filter(Rooms.room_category == room_category)
    if min_price is not None:
        query = query.filter(Rooms.price >= min_price)
    if max_price is not None:
        query = query.filter(Rooms.price <= max_price)
    # NOTE: your current route has no guest-capacity filter at all. Adding
    # this here as an opt-in extra for the agent -- confirm `max_occupancy`
    # is the right column name, and remove this block if you'd rather keep
    # search behaviour identical to today for both the page and the agent.
    if guests is not None:
        query = query.filter(Rooms.max_occupancy >= guests)
 
    if arrival and departure:
        try:
            arrival_date = datetime.strptime(arrival, "%Y-%m-%d").date()
            departure_date = datetime.strptime(departure, "%Y-%m-%d").date()
        except ValueError:
            return {"query": None, "error": "invalid_dates"}
 
        if arrival_date >= departure_date:
            return {"query": None, "error": "departure_before_arrival"}
 
        candidate_rooms = query.all()
        available_room_ids = [room.id for room in candidate_rooms
                               if is_available(room.id, arrival_date, departure_date)]
        if not available_room_ids:
            return {"query": query.filter(Rooms.id == -1), "error": "no_availability"}
 
        query = query.filter(Rooms.id.in_(available_room_ids))
 
    return {"query": query, "error": None}


def serialize_room(room):
    '''
    converts a Rooms SQLAlchemy object into a plain JSON-safe dict 
    (id, name, location, category, price, max_occupancy, image_url), 
    using room.image1 for the photo. It exists so the AI agent's tools 
    (search_rooms, show_room_photo) can hand room data to the LLM and, ultimately,
    the chat widget — since raw SQLAlchemy model instances can't be json.dumps'd 
    directly
    '''
    # Rooms model has 6 image fields (image1..image6) -- always use image1
    # as the representative photo for chat cards.
    image_url = None
    if getattr(room, "image1", None):
        image_url = url_for('static', filename='userpics/roompics/' + room.image1)

    return {
        "id": room.id,
        "name": getattr(room, "room_name", None) or f"Room {room.id}",
        "location": room.room_location,
        "category": room.room_category,
        "price": float(room.price) if room.price is not None else None,
        "max_occupancy": room.max_occupancy,
        "image_url": image_url,
    }