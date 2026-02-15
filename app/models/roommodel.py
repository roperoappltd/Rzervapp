from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin, current_user
from flask import current_app, render_template

class Rooms(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # ------------------------------------------------------------------------------------- 
    room_name = db.Column(db.String(30), nullable=False, unique=True)
    room_location = db.Column(db.String(30), nullable=False)
    room_category = db.Column(db.String(30), nullable=False)
    image1 = db.Column(db.String(30), nullable=False, default='roomdef1.jpeg')
    image2 = db.Column(db.String(30), nullable=False, default='roomdef2.jpg')
    image3 = db.Column(db.String(30), nullable=False, default='roomdef3.jpeg')
    short_desc = db.Column(db.String(100), nullable=False)
    room_size = db.Column(db.String(20), nullable=False)
    max_occupancy = db.Column(db.Integer)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="available")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # def __init__(self, room_name, room_location, room_category, image1, image2, image3, short_desc, room_size, max_occupancy, price, description, status="available"):
    #     self.room_name = room_name
    #     self.room_location = room_location
    #     self.room_category = room_category
    #     self.image1 = image1
    #     self.image2 = image2
    #     self.image3 = image3
    #     self.short_desc = short_desc
    #     self.room_size = room_size
    #     self.max_occupancy = max_occupancy
    #     self.price = price
    #     self.description = description
    #     self.status = status

    def get_all(cls):
        rooms = cls.query.all()
        return rooms
  
    def find_by_id(cls, id):
        room = cls.query.filter_by(id=id)
        return room

    def __repr__(self):
        return f"Rooms('{self.room_name}','{self.room_location}','{self.room_category}','{self.short_desc}'\
                      '{self.room_size}','{self.max_occupancy}','{self.price}','{self.status}'\
                      '{self.description}')"

    # def data(self): # room_category
    #     return {
    #     "room_name": self.room_name,  
    #     "room_location": self.room_location,
    #     "room_category": self.room_category,  
    #     "image1": self.image1,
    #     "image2": self.image2,
    #     "image3": self.image3,
    #     "short_desc": self.short_desc,
    #     "room_size": self.room_size,
    #     "max_occupancy": self.max_occupancy,
    #     "price": self.price,
    #     "description": self.description,
    #     "status": self.status,
    #     }