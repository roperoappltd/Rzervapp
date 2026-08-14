from datetime import datetime
from app import db
from flask import current_app, render_template

class Rooms(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # ------------------------------------------------------------------------------------- 
    room_name = db.Column(db.String(30), nullable=False)  # FIXED: was globally unique=True -- two hosts could reasonably want the same name
    room_location = db.Column(db.String(30), nullable=False, index=True)  # NEW: index, this is a search filter
    # room_address = db.Column(db.String(150), nullable=True)
    room_country = db.Column(db.String(50), nullable=True)
    room_category = db.Column(db.String(30), nullable=False, index=True)  # NEW: index, this is a search filter
    image1 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image2 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image3 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image4 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image5 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image6 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    short_desc = db.Column(db.String(100), nullable=False)
    room_size = db.Column(db.String(20), nullable=False)
    max_occupancy = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)  # FIXED: was room_price / Float -- kept as `price` to match existing code in search.py and create_booking()
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Available")  # Available - Maintenance - Hidden
    rule1 = db.Column(db.String(50), nullable=True)
    rule2 = db.Column(db.String(50), nullable=True)
    rule3 = db.Column(db.String(50), nullable=True)
    latitude = db.Column(db.Float, nullable=True)   # FIXED: nullable -- geocoding can fail even after inviting the host to retry; NULL doubles as the admin follow-up flag (query WHERE latitude IS NULL)
    longitude = db.Column(db.Float, nullable=True)
    room_currency = db.Column(db.String(3), nullable=False)  # FIXED: was nullable=True -- required by the currency conversion chain in create_booking()
    # =======================================================================
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_extra = db.relationship('Roomextra', backref='rooms', uselist=False)
    room_review = db.relationship('Roomreviews', backref='rooms', lazy=True)
    room_booking = db.relationship('Bookings', backref='rooms', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'room_name', name='uq_room_name_per_host'),
        db.CheckConstraint('max_occupancy > 0', name='ck_room_occupancy_positive'),
        db.CheckConstraint('price > 0', name='ck_room_price_positive'),
        db.CheckConstraint('latitude BETWEEN -90 AND 90', name='ck_room_latitude_range'),
        db.CheckConstraint('longitude BETWEEN -180 AND 180', name='ck_room_longitude_range'),
    )
    def get_all(cls):
        rooms = cls.query.all()
        return rooms
  
    def find_by_id(cls, id):
        room = cls.query.filter_by(id=id)
        return room

    def __repr__(self):
        return f"Rooms('{self.room_name}', '{self.room_location}', '{self.room_category}'\
                      '{self.short_desc}', '{self.image1}', '{self.image2}', '{self.image3}'\
                      '{self.image4}', '{self.image5}', '{self.image6}', '{self.room_size}'\
                      '{self.max_occupancy}', '{self.price}', '{self.status}'\
                      '{self.description}', '{self.room_currency}, '{self.room_country}'')"

class RoomBlock(db.Model):
    __tablename__ = 'roomblock'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    reason = db.Column(db.String(100))
    notes = db.Column(db.Text)

class Roomextra(db.Model):
    __tablename__ = 'roomextra'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    # services  
    resto = db.Column(db.String(20), nullable=False)
    bar = db.Column(db.String(10), nullable=False)
    spa = db.Column(db.String(10), nullable=False)
    shop = db.Column(db.String(10), nullable=False)
    concierge = db.Column(db.String(10), nullable=False)
    car = db.Column(db.String(10), nullable=False)
    # Amenities
    sleeping = db.Column(db.String(10), nullable=False)
    hot_water = db.Column(db.String(10), nullable=False)
    smart_tv = db.Column(db.String(10), nullable=False)
    internet = db.Column(db.String(10), nullable=False)
    kitchen = db.Column(db.String(10), nullable=False)
    towels = db.Column(db.String(10), nullable=False)
    # comfort life style
    aircon = db.Column(db.String(10), nullable=False)
    pool = db.Column(db.String(10), nullable=False)
    workspace = db.Column(db.String(10), nullable=False)
    washing = db.Column(db.String(10), nullable=False)
    Sport = db.Column(db.String(10), nullable=False)
    parking = db.Column(db.String(10), nullable=False)
    # ====================================================================
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), unique=True)
    
    def __repr__(self):
        return f"Roomextra('{self.resto}','{self.bar}','{self.spa}'\
                      '{self.shop}', '{self.concierge}', '{self.sleeping}'\
                      '{self.hot_water}','{self.tv}', '{self.kitchen}'\
                      '{self.towels}')"

# Creating the user db model
class Roomreviews(db.Model):
    '''This class is a User model'''
    # adding the columns
    __tablename__ = 'roomreviews'
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rate_us = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Published')  # Published - Flagged - Removed
    message = db.Column(db.String(200), nullable=False)

    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)  # NEW: enforces one review per completed stay -- app code must still verify booking.user_id/room_id match before insert, the DB can't check that cross-table condition itself
    # Cached running total, NOT computed live via COUNT() on every page load.
    # Displaying it costs nothing extra -- just read the column. Only the
    # toggle action below touches ReviewHelpful directly.
    helpful_count = db.Column(db.Integer, nullable=False, default=0)
    # ===========================================================================
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))  # FIXED: was backref='user', would have collided/misled (User.user returning itself)
    booking = db.relationship('Bookings', backref=db.backref('review', uselist=False))

    __table_args__ = (
        db.CheckConstraint('rate_us BETWEEN 1 AND 5', name='ck_review_rating_range'),
    )
    
    # Display output
    def __repr__(self):
        return f"Roomreviews('{self.status}','{self.message}','{self.rate_us}')"

class GuestReviews(db.Model):
    __tablename__ = 'guestreviews'
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rate_us = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='Published')  # Published - Flagged - Removed, same convention as Roomreviews

    # Same enforcement pattern as Roomreviews.booking_id: unique=True
    # guarantees one review per completed stay -- can't be reviewed twice.
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)   # the reviewer
    guest_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # the person being reviewed

    host = db.relationship('User', foreign_keys=[host_id], backref=db.backref('guest_reviews_written', lazy=True))
    guest = db.relationship('User', foreign_keys=[guest_id], backref=db.backref('reviews_received', lazy=True))
    booking = db.relationship('Bookings', backref=db.backref('guest_review', uselist=False))

    __table_args__ = (
        db.CheckConstraint('rate_us BETWEEN 1 AND 5', name='ck_guestreview_rating_range'),
    )
    # Display output
    def __repr__(self):
        return f"Roomreviews('{self.status}','{self.message}','{self.rate_us}')"
    
class ReviewHelpful(db.Model):
    '''
        One row per user's helpful-vote on a review. The unique constraint
        both prevents double-voting and is what a toggle (vote/un-vote) checks
        against.
    '''
    __tablename__ = 'review_helpful'
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('roomreviews.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('review_id', 'user_id', name='uq_review_helpful_once'),
    )
    # Display output
    def __repr__(self):
        return f"ReviewHelpful('{self.review_id}','{self.user_id}','{self.created_at}')"

class RoomView(db.Model):
    '''One row per deduped view (see roomdetail()'s per-room-per-day
    session check). This is intentionally a log, not a running counter --
    a counter has no time dimension and can't power a trend chart.'''
    __tablename__ = 'room_view'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False, index=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Display output
    def __repr__(self):
        return f"RoomView('{self.room_id}','{self.viewed_at}','{self.id}')"

# class Deals(db.Model):
#     __tablename__ = 'deals'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     start_date = db.Column(db.Date)
#     end_date = db.Column(db.Date)
#     description = db.Column(db.Text)
#     discount_percent = db.Column(db.Integer)
#     image_file = db.Column(db.String(100))
#     active = db.Column(db.Boolean, default=True)
    
#     # Display output
#     def __repr__(self):
#         return f"Deals('{self.name}','{self.start_date}','{self.end_date}'\
#                        '{self.description}', '{self.discount_percent}', \
#                        '{self.end_date}', '{self.active}')"


class Deals(db.Model):
    __tablename__ = 'deals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)  # AMENDED: was nullable=False -- host-set discounts don't need a campaign name, only the 3 existing platform campaigns do
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True, unique=True, index=True)  # NEW: NULL = global platform campaign (existing 3), set = this specific room's host-set discount. unique=True enforces one active discount per room; NULL room_id rows are exempt from the uniqueness check (standard SQL behavior), so multiple global campaigns still coexist fine.
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)
    discount_percent = db.Column(db.Integer)
    image_file = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    # =============================================================================
    room = db.relationship('Rooms', backref=db.backref('host_deal', uselist=False))
    
    # Display output
    def __repr__(self):
        return f"Deals('{self.name}','{self.start_date}','{self.end_date}'\
                       '{self.description}', '{self.discount_percent}', \
                       '{self.end_date}', '{self.active}')"