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
    booking_num = db.Column(db.String(20), nullable=False, unique=True)  # FIXED: was nullable=True with no uniqueness -- this is the customer-facing reference number
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
    status_reason = db.Column(db.String(50), nullable=True)  # NEW: explicit audit trail for WHY a status change happened (e.g. 'pending_timeout') -- status alone only tells you the current state, not the cause, and that becomes ambiguous the moment a second mechanism could ever produce the same status
    active = db.Column(db.Boolean, default=False)

    serv_charge = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=True, default=0.00) # 3 to 5% of total amount
    serv_charge_gbp = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=True, default=0.00)
    serv_charge_currency = db.Column(db.String(3), nullable=True)  # NEW: currency serv_charge is denominated in
    serv_charge_exchange_rate = db.Column(db.Numeric(18, 8), nullable=True)  # NEW: serv_charge_currency -> GBP
    # =============================================================================
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)

    # No cascade on any financial relationship -- deleting a Bookings row
    # (which should really only happen in dev/test cleanup, never in real
    # app flow -- cancellations are a status change, not a DELETE) must
    # never silently take payment/earning/refund records with it.
    payment = db.relationship('Payments', backref='booking', uselist=False)
    earning = db.relationship('HostEarning', backref='booking', uselist=False)  # FIXED: was 'earnings' (plural) with backref='host' (misleading -- .host returned a Booking, not a User); also FIXED uselist since HostEarning.booking_id is unique=True, a true one-to-one
    refund = db.relationship('Refund', backref='booking', uselist=False)

    # Not a financial record -- safe to cascade-delete.
    conversation = db.relationship("Conversation", backref="booking", uselist=False,
                                    cascade="all, delete-orphan")

    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'), nullable=True, default=None)
    deal = db.relationship('Deals')

    def get_all(cls):
        bookings = cls.query.all()
        return bookings
  
    def find_by_id(cls, id):
        booking = cls.query.filter_by(id=id)
        return booking

    def __repr__(self):
        return f"Bookings('{self.arrival}', '{self.departure}', '{self.num_guests}'\
                    '{self.room_type}', '{self.ad_info}', '{self.primary_guest}'\
                    '{self.pguest_email}', '{self.pguest_phone}', '{self.booking_num}'\
                    '{self.serv_charge}', '{self.serv_charge_gbp}')"

class Payments(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # ------------------------------------------------------------------------------------- 
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pay_method = db.Column(db.String(30), nullable=False, default='Cash on Arrival')

    room_price_original = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    room_price_gbp = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    room_price_currency = db.Column(db.String(3), nullable=False)
    room_price_exchange_rate = db.Column(db.Numeric(18,8))   # room_price_currency -> accounting_currency
    book_days = db.Column(db.Integer, nullable=False, default=1)

    discount_gbp = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True, default=0.00)
    discount_host = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True, default=0.00)
    discount_funded_by = db.Column(db.String(20), nullable=True)

    transac_fee_host = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True)
    transac_fee_gbp = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True)

    # NEW: Paystack's own processing fee -- kept separate from
    # transac_fee_* above (Jambo's own 15% commission, calculated
    # independently of any payment gateway). Never touches
    # HostEarning.host_earning_* at all, since Jambo absorbs this cost
    # itself rather than passing it to the host. Populated once
    # Paystack's verify endpoint confirms the transaction, using the
    # real fee amount it reports -- not a value Jambo calculates itself,
    # since the rate varies by channel (1.95% mobile money, 3.2% local
    # card, 3.8% international card) and could drift from Paystack's
    # own figures if replicated independently. so that records are consistent.
    gateway_fee_guest = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True)
    gateway_fee_gbp = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=True)
    gateway_channel = db.Column(db.String(30), nullable=True)
    gateway_reference = db.Column(db.String(60), nullable=True)

    total_paid_guest = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    payment_currency = db.Column(db.String(3))

    accounting_amount = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False) # convert total paid in GBP
    accounting_currency = db.Column(db.String(3), default="GBP")

    pay_exchange_rate = db.Column(db.Numeric(18,8), nullable=False)  # payment_currency -> accounting_currency
    rate_captured_at = db.Column(db.DateTime, default=datetime.utcnow)  # shared timestamp for both, since they're fetched together

    status = db.Column(db.String(20), nullable=True, default='Unpaid')
    points_earned = db.Column(db.Integer, nullable=True, default=0)
   
    # ==========================================================================
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'), nullable=True)
    voucher = db.relationship('Vouchers', back_populates='payment')
    host_earning = db.relationship('HostEarning', backref='payment', 
                                   uselist=False, cascade="all, delete-orphan")
    refund = db.relationship('Refund', backref='payments',uselist=False,
                                        cascade="all, delete-orphan")
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id', name='fk_payments_deal_id'), 
                                                nullable=True)

    def get_all(cls):
        payments = cls.query.all()
        return payments
  
    def find_by_id(cls, id):
        payment = cls.query.filter_by(id=id)
        return payment

    def __repr__(self):
        return f"Payments('{self.payment_date}', '{self.pay_method}', '{self.room_price_gbp}'\
                    '{self.book_days}', '{self.discount_funded_by}', '{self.transac_fee_host}')\
                    '{self.total_paid_guest}', '{self.transac_fee_gbp}'), '{self.points_earned}'\
                    '{self.payment_currency}', '{self.status}', '{self.accounting_amount}')"

class Vouchers(db.Model):
    __tablename__ = 'vouchers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    code = db.Column(db.String(10), nullable=False)
    funded_by = db.Column(db.String(20), nullable=False)
    value = db.Column(db.Numeric(10,2 , asdecimal=True), nullable=False)
    is_active = db.Column(db.String(6), nullable=True, default='True')
    #payment = db.relationship('Payments', backref='vouchers')
    payment = db.relationship('Payments', back_populates='voucher', lazy=True)

    def __repr__(self):
        return f"Vouchers('{self.start_date}', '{self.end_date}', '{self.code}'\
                    '{self.value}', '{self.is_active}', '{self.funded_by}')"

class VoucherUsage(db.Model):
    __tablename__ = 'voucherusage'
    __table_args__ = (
        db.UniqueConstraint('voucher_id', 'user_id', name='uq_voucher_user_usage'),)
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payment_id = db.Column(db.Integer,db.ForeignKey('payments.id'),nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return f"VoucherUsage('{self.payment_id}', '{self.voucher_id}', '{self.used_at}'\
                    '{self.user_id}')"

class HostEarning(db.Model):
    __tablename__ = 'hostearning'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    gross_amount_host = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)
    gross_amount_gbp = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)
    # NEW: mirrors Payments.discount_gbp / discount_host, but only populated
    # when discount_funded_by == 'host' on the related Payment -- i.e. this
    # is the portion of the discount that actually reduced this host's
    # earning, as opposed to a platform-funded discount that doesn't touch
    # host_earning_* at all.
    discount_host = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=True, default=0.00)
    discount_gbp = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=True, default=0.00)

    host_earning_host = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)
    host_earning_gbp = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)
    host_currency = db.Column(db.String(3))

    voucher_amount_gbp = db.Column(db.Numeric(10, 2, asdecimal=True), default=0)
    voucher_amount_host = db.Column(db.Numeric(10, 2, asdecimal=True), default=0)

    platform_fee_host = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)
    platform_fee_gbp = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)

    # NEW: per-notification charge for hosts who've opted into paid
    # booking notifications (SMS or WhatsApp). Populated only when a
    # notification was actually sent for this specific booking --
    # nullable, since most bookings won't have one (host not opted in,
    # send failed, or no valid phone number). notification_channel_used
    # records which channel this particular booking actually used, in
    # case the host's own preference changes between bookings.
    notification_fee_host = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=True, default=0.00)
    notification_fee_gbp = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=True, default=0.00)
    notification_channel_used = db.Column(db.String(10), nullable=True)

    exchange_rate = db.Column(db.Numeric(18, 8))  # host_currency -> GBP; correct as a single field,
                                                  # this table never involves a third payment currency
    status = db.Column(db.String(20), default='Pending')  # Paid - Pending - Refunded
    #----------------------------------------------------------------------------
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False, unique=True)

    def __repr__(self):
        return f"HostEarning('{self.gross_amount_host}', '{self.voucher_amount_host}',\
                '{self.host_earning_host}', '{self.exchange_rate}', '{self.status}',\
                '{self.platform_fee_gbp}')"

class Withdrawal(db.Model):
    __tablename__ = 'withdrawal'
    id = db.Column(db.Integer, primary_key=True)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

    amount_host = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)
    amount_gbp = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)
    host_currency = db.Column(db.String(3), nullable=False)  # NEW: currency amount_host is denominated in

    withdraw_xchange_rate = db.Column(db.Numeric(18, 8), nullable=False)  # FIXED: was Numeric(10,2), truncated most real rates

    payout_method = db.Column(db.String(30), nullable=True)     # NEW: e.g. 'Bank Transfer', 'Mobile Money'
    payout_reference = db.Column(db.String(120), nullable=True)  # NEW: account number / mobile money number / reference used for this specific payout

    status = db.Column(db.String(20), default='Pending')
    processed_at = db.Column(db.DateTime, nullable=True)
    #----------------------------------------------------------------------------
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    def __repr__(self):
        return f"Withdrawal('{self.amount_host}', '{self.amount_gbp}',\
                '{self.withdraw_xchange_rate}, '{self.host_currency}')"
    
class Refund(db.Model):
    __tablename__ = 'refund'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    refunded_at = db.Column(db.DateTime, nullable=True)  # set only when status becomes 'Paid'

    amount_refund_guest = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)  # refunded to the guest, in the currency THEY originally paid with (matches Payment.payment_currency for this booking)
    amount_refund_gbp = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)
    refund_currency = db.Column(db.String(3), nullable=False)  # must match the related Payment.payment_currency -- you refund in the currency that was actually charged
    exchange_rate = db.Column(db.Numeric(18, 8))  # refund_currency -> GBP, captured at refund time

    reason = db.Column(db.String(255), nullable=False, default='24h Flexible cancellation')

    # Pending -> Approved -> Paid (refunded_at set on this transition)
    #         -> Rejected (terminal, refunded_at stays None)
    status = db.Column(db.String(20), default='Pending')
    # ==========================================================================
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # FIXED: was unique=True, blocked a user from ever getting a 2nd refund

    def __repr__(self):
        return f"Refund('{self.refunded_at}', '{self.amount_refund_guest}',\
                '{self.reason}', '{self.amount_refund_gbp}', '{self.exchange_rate}')"

class ExchangeRate(db.Model):
    __tablename__ = "exchange_rates"
    __table_args__ = (db.UniqueConstraint("base_currency","target_currency", 
                                          name="unique_exchange_rate"),)
    id = db.Column(db.Integer, primary_key=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                            onupdate=datetime.utcnow)
    base_currency = db.Column(db.String(3), nullable=False)
    target_currency = db.Column(db.String(3), nullable=False)
    rate = db.Column(db.Numeric(18, 8), nullable=False)

    def __repr__(self):
        return f"ExchangeRate('{self.base_currency}', '{self.target_currency}',\
                '{self.rate}')"