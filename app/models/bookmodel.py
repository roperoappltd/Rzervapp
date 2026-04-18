from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin, current_user
from flask import current_app, render_template
#from .usermodel import User
#from .roommodel import Rooms

class Bookings(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # ------------------------------------------------------------------------------------- 
    arrival = db.Column(db.Date, nullable=False)
    departure = db.Column(db.Date, nullable=False)
    num_guests = db.Column(db.Integer, nullable=False)
    #num_rooms = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(30), nullable=False)
    ad_info = db.Column(db.Text, nullable=False, default='What would you like?')
    primary_guest = db.Column(db.String(30), nullable=False)
    pguest_email = db.Column(db.String(30), nullable=False)
    pguest_phone = db.Column(db.String(30), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    payment = db.relationship('Payments', backref='bookings', uselist=False)

    def get_all(cls):
        bookings = cls.query.all()
        return bookings
  
    def find_by_id(cls, id):
        booking = cls.query.filter_by(id=id)
        return booking

    def __repr__(self):
        return f"Bookings('{self.arrival}', '{self.departure}', '{self.num_guests}'\
                    '{self.room_type}', '{self.ad_info}', '{self.primary_guest}'\
                    '{self.pguest_email}', '{self.pguest_phone}')"

class Payments(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    #created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # ------------------------------------------------------------------------------------- 
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pay_method = db.Column(db.String(30), nullable=False)
    price_per_night = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    book_days = db.Column(db.Integer, nullable=False, default=1)
    discount = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True, default=0.00)
    serv_charge = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True, default=0.00)
    total_paid = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    rzerv_points = db.Column(db.Integer, nullable=True, default=20)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'), nullable=True)

    def get_all(cls):
        payments = cls.query.all()
        return payments
  
    def find_by_id(cls, id):
        payment = cls.query.filter_by(id=id)
        return payment

    def __repr__(self):
        return f"Payments('{self.payment_date}', '{self.pay_method}', '{self.price_per_night}'\
                    '{self.book_days}', '{self.discount}','{self.serv_charge}'\
                    '{self.total_paid}', '{self.rzerv_points}')"

class Vouchers(db.Model):
    __tablename__ = 'vouchers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # ------------------------------------------------------------------------------------- 
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    code = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False, default=0.00)
    payment = db.relationship('Payments', backref='vouchers')


    def __repr__(self):
        return f"Vouchers('{self.start_date}', '{self.end_date}', '{self.code}'\
                    '{self.value}')"