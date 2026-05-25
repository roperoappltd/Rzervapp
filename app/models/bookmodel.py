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
    booking_num = db.Column(db.String(20), nullable=True)
    arrival = db.Column(db.Date, nullable=False)
    departure = db.Column(db.Date, nullable=False)
    num_guests = db.Column(db.Integer, nullable=False)
    #num_rooms = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(30), nullable=False)
    ad_info = db.Column(db.Text, nullable=False, default='What would you like?')
    primary_guest = db.Column(db.String(30), nullable=False)
    pguest_email = db.Column(db.String(30), nullable=False)
    pguest_phone = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=True, default='Pending')
    active = db.Column(db.String(5), default='False')
    serv_charge = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True, default=0.00)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    payment = db.relationship('Payments', backref='bookings', uselist=False)
    earnings = db.relationship('HostEarning', backref='host', lazy=True)
    refund = db.relationship('Refund', backref='booking', uselist=False)

    def get_all(cls):
        bookings = cls.query.all()
        return bookings
  
    def find_by_id(cls, id):
        booking = cls.query.filter_by(id=id)
        return booking

    def __repr__(self):
        return f"Bookings('{self.arrival}', '{self.departure}', '{self.num_guests}'\
                    '{self.room_type}', '{self.ad_info}', '{self.primary_guest}'\
                    '{self.pguest_email}', '{self.pguest_phone}', '{self.booking_num}')"

class Payments(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # ------------------------------------------------------------------------------------- 
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pay_method = db.Column(db.String(30), nullable=False, default='Cash on Arrival')
    price_per_night = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    book_days = db.Column(db.Integer, nullable=False, default=1)
    discount = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True, default=0.00)
    #serv_charge = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True, default=0.00)
    transac_fee = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True)
    total_paid = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    rzerv_points = db.Column(db.Integer, nullable=True, default=20)
    status = db.Column(db.String(20), nullable=True, default='Unpaid')
    #code = db.Column(db.String(10), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    #voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'), nullable=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'), nullable=True)
    voucher = db.relationship('Vouchers', back_populates='payment')
    host_earning = db.relationship('HostEarning', backref='payment', uselist=False)
    refund = db.relationship('Refund', backref='payment',uselist=False)

    def get_all(cls):
        payments = cls.query.all()
        return payments
  
    def find_by_id(cls, id):
        payment = cls.query.filter_by(id=id)
        return payment

    def __repr__(self):
        return f"Payments('{self.payment_date}', '{self.pay_method}', '{self.price_per_night}'\
                    '{self.book_days}', '{self.discount}', '{self.status}'\
                    '{self.total_paid}', '{self.rzerv_points}')"

class Vouchers(db.Model):
    __tablename__ = 'vouchers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    code = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    is_active = db.Column(db.String(6), nullable=True, default='True')
    #payment = db.relationship('Payments', backref='vouchers')
    payment = db.relationship('Payments', back_populates='voucher', uselist=False)


    def __repr__(self):
        return f"Vouchers('{self.start_date}', '{self.end_date}', '{self.code}'\
                    '{self.value}', '{self.is_active}')"

class VoucherUsage(db.Model):
    __tablename__ = 'voucherusage'
    __table_args__ = (
        db.UniqueConstraint('voucher_id', 'user_id', name='uq_voucher_user_usage'),)
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payment_id = db.Column(db.Integer,db.ForeignKey('payments.id'),nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)

class HostEarning(db.Model):
    __tablename__ = 'hostearning'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    gross_amount = db.Column( db.Numeric(10, 2), nullable=False)
    voucher_amount = db.Column(db.Numeric(10, 2), default=0 )
    platform_fee = db.Column( db.Numeric(10, 2), nullable=False)
    net_earning = db.Column(db.Numeric(10, 2), nullable=False)
    # Paid - Pending - Refunded  
    status = db.Column(db.String(20), default='Pending')
    #----------------------------------------------------------------------------
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column( db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    payment_id = db.Column( db.Integer, db.ForeignKey('payments.id'),nullable=False, unique=True)

    def __repr__(self):
        return f"HostEarning('{self.gross_amount}', '{self.voucher_amount}',\
                '{self.net_earning}')"

class Withdrawal(db.Model):
    __tablename__ = 'withdrawal'
    id = db.Column(db.Integer, primary_key=True)
    requested_at = db.Column(db.DateTime,default=datetime.utcnow)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    #-------------------------------------------------------------
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f"Withdrawal('{self.amount}', '{self.status}',\
                '{self.requested_at}')"
    
class Refund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    refunded_at = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.String(255), nullable=False, default='24h Flexible cancellation')
    # pending / approved / rejected / completed/ Paid
    status = db.Column(db.String(20), default='pending')
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False, unique=True)
    user_id = db.Column( db.Integer,db.ForeignKey('user.id'), nullable=False, unique=True)
    
    def __repr__(self):
        return f"Refund('{self.refunded_at}', '{self.amount}',\
                '{self.reason}', '{self.status}')"
    