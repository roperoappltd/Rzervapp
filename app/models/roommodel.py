from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin, current_user
from flask import current_app, render_template
#from .bookmodel import Bookings

class Rooms(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # ------------------------------------------------------------------------------------- 
    room_name = db.Column(db.String(30), nullable=False, unique=True)
    room_location = db.Column(db.String(30), nullable=False)
    room_category = db.Column(db.String(30), nullable=False)
    image1 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image2 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image3 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image4 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image5 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    image6 = db.Column(db.String(20), nullable=False, default='roomdef1.jpg')
    short_desc = db.Column(db.String(100), nullable=False)
    room_size = db.Column(db.String(20), nullable=False)
    max_occupancy = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="available")
    usp1 = db.Column(db.String(50), nullable=True)
    usp2 = db.Column(db.String(50), nullable=True)
    usp3 = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_extra = db.relationship('Roomextra', backref='rooms', uselist=False)
    room_review = db.relationship('Roomreviews', backref='rooms', lazy=True)
    room_booking = db.relationship('Bookings', backref='rooms', lazy=True)
    #room_payment = db.relationship('Payments', backref='rooms', lazy=True)

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
                      '{self.max_occupancy}', '{self.price}', '{self.status}', '{self.description}')"

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
    sleeping = db.Column(db.String(20), nullable=False)
    hot_water = db.Column(db.String(10), nullable=False)
    tv = db.Column(db.String(10), nullable=False)
    internet = db.Column(db.String(10), nullable=False)
    kitchen = db.Column(db.String(10), nullable=False)
    towels = db.Column(db.String(10), nullable=False)
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
    status = db.Column(db.String(20), default='Verified')
    message = db.Column(db.String(200), nullable=False)
    
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    #post = db.relationship('Post', backref=db.backref('post', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('user', lazy=True))
    #user = db.relationship('User',  back_populates='user', lazy=True)
    
    # Display output
    def __repr__(self):
        return f"Roomreviews('{self.status}','{self.message}','{self.rate_us}')"