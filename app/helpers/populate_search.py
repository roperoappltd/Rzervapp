from app import db
from app.models.roommodel import Rooms


def populate_search_choices(form):
    locations = (db.session.query(Rooms.room_location).distinct()
                                 .order_by(Rooms.room_location).all())
    boroughs = (db.session.query(Rooms.borough).distinct()
                                 .order_by(Rooms.borough).all())
    categories = (db.session.query(Rooms.room_category).distinct()
                                  .order_by(Rooms.room_category).all())
    form.room_location.choices = [
                                 ('', 'All Locations')
                                 ] + [(loc[0], loc[0]) for loc in locations]
    form.borough.choices = [
                                 ('', 'All Boroughs')
                                 ] + [(b[0], b[0]) for b in boroughs]
    form.room_category.choices = [
                                 ('', 'All Categories')
                                 ] + [(cat[0], cat[0]) for cat in categories]