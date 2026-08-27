from datetime import datetime, date
from app import db, login_manager
from flask_login import UserMixin, current_user
from flask import current_app, render_template
from itsdangerous import URLSafeTimedSerializer as Serializer
from wtforms.validators import ValidationError
#from .bookmodel import Bookings


# defining a function decorator that fectch the user by id 
# callback to reload the user object 
@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))

 
class User(db.Model, UserMixin):
    '''This class is a User model'''
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
 
    # Personal detail
    first_name = db.Column(db.String(40), nullable=False)
    last_name = db.Column(db.String(40), nullable=False)
    gender = db.Column(db.String(30), nullable=True, default='Change me')  # FIXED: was db.String with no length -- SQLite tolerates this, MySQL requires an explicit VARCHAR length and fails outright without one
    dob = db.Column(db.Date, nullable=False)  # 18+ enforced via validate_dob_minimum_age below, not a DB constraint -- MySQL disallows non-deterministic functions like CURRENT_DATE in CHECK constraints
 
    # Location
    address = db.Column(db.String(100), nullable=True, default='Change me')
    city = db.Column(db.String(40), nullable=True, default='Change me')
    zip_code = db.Column(db.String(10), nullable=True, default='Change me')
    country = db.Column(db.String(40), nullable=True, default='Change me')
 
    # Contact info
    company_name = db.Column(db.String(30), nullable=True, default='Change me')
    # FIXED: was db.String(20) -- the generated filename is 16 hex
    # chars + extension (secrets.token_hex(8)), which exactly hits 20
    # for a 4-char extension like .jpg with zero headroom, and would
    # exceed it entirely for a 5-char one like .jpeg or .webp (both
    # very common, especially .webp from phone cameras) -- the same
    # "Data too long" crash as the room images, just not yet triggered.
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')
    phone = db.Column(db.String(30), nullable=True, default='Change me')
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # bcrypt hashes are 60 chars; sized with headroom for any future hashing algo change
 
    terms_accepted = db.Column(db.Boolean, nullable=False, default=False)
    terms_accepted_at = db.Column(db.DateTime, nullable=True)
 
    is_admin = db.Column(db.Boolean, nullable=False, default=False)  # single source of truth for admin access -- the old `role` string field was removed entirely
 
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    email_verified_at = db.Column(db.DateTime, nullable=True)
 
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)  # brute-force lockout tracking
    locked_until = db.Column(db.DateTime, nullable=True)  # set when lockout triggers; NULL means not locked
 
    last_login = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)  # NULL = active account; set = soft-deleted
 
    aboutme = db.Column(db.String(200), nullable=True, default='Tell the word something nice about yourself')
    rzerv_points = db.Column(db.Integer, nullable=False, default=0)
    language = db.Column(db.String(5), default="en")
    preferred_currency = db.Column(db.String(3), default="GBP")

    # Single choice field rather than separate booleans -- enabling
    # both SMS and WhatsApp would double-charge for a redundant
    # notification about the same event.
    notification_channel = db.Column(db.String(10), nullable=False, default='none')
 
    # ==============================================================
    roomads = db.relationship('Rooms', backref='user', lazy=True)
    mybooking = db.relationship('Bookings', backref='user', lazy=True)
    mypayment = db.relationship('Payments', backref='user', lazy=True)
    earnings = db.relationship('HostEarning', backref='host', lazy=True)
    withdrawals = db.relationship('Withdrawal', backref='host', lazy=True)
    refunds = db.relationship('Refund', backref='user', lazy=True)
 
    # ------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------
    @property
    def is_active(self):
        '''Overrides UserMixin's default (always True). Flask-Login's
        login_user() checks this automatically and refuses to log in an
        inactive user -- first of two layers blocking a soft-deleted
        account; the second is the explicit check in the login route.'''
        return self.deleted_at is None
 
    def soft_delete(self):
        '''Flags the account and scrubs identifying fields, WITHOUT
        touching any row that references this user_id (Bookings,
        Payments, HostEarning, Withdrawal, Refund) -- those relationships
        were deliberately built without cascade delete, so financial
        history survives account deletion.'''
        self.deleted_at = datetime.utcnow()
        self.email = f"deleted_{self.id}@deleted.jambo"
        self.username = f"deleted_user_{self.id}"
        self.first_name = "Deleted"
        self.last_name = "User"
        self.gender = None
        self.dob = None
        self.address = None
        self.city = None
        self.zip_code = None
        self.country = None
        self.company_name = None
        self.phone = None
        self.aboutme = None
        self.image_file = "default.jpg"
 
    # ------------------------------------------------------------
    # Password reset / email verification tokens
    # ------------------------------------------------------------
    def get_reset_token(self, max_age=1800):
        '''Generates a password-reset token.'''
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id, 'purpose': 'reset_password'})
 
    @staticmethod
    def verify_reset_token(token):
        '''Validates a password-reset token.'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=1800)
            if data.get('purpose') != 'reset_password':  # rejects a verify-email token replayed here
                return None
            user_id = data['user_id']
        except:
            return None
        return User.query.get(user_id)
 
    def get_verification_token(self, max_age=86400):
        '''Generates an email-verification token. 24h default -- less
        time-sensitive than a password reset, so a longer window is fine.'''
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id, 'purpose': 'verify_email'})
 
    @staticmethod
    def verify_verification_token(token, max_age=86400):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=max_age)
            if data.get('purpose') != 'verify_email':  # rejects a reset-password token replayed here
                return None
            user_id = data['user_id']
        except:
            return None
        return User.query.get(user_id)
 
    # ------------------------------------------------------------
    # Form validators
    # ------------------------------------------------------------
    @staticmethod
    def validate_dob_minimum_age(form, field):
        '''WTForms validator -- attach on the signup form:
        dob = DateField(..., validators=[DataRequired(), User.validate_dob_minimum_age])'''
        if field.data is None:
            return
        today = date.today()
        age = today.year - field.data.year - ((today.month, today.day) < (field.data.month, field.data.day))
        if age < 18:
            raise ValidationError('You must be at least 18 years old to register.')
 
    def __repr__(self):
        return f"User('{self.first_name}','{self.last_name}','{self.gender}','{self.dob}'\
                      '{self.address}','{self.city}','{self.zip_code}','{self.country}'\
                      '{self.company_name}, {self.phone}','{self.username}','{self.email}'\
                      '{self.image_file}', '{self.is_admin}', '{self.aboutme}')"
                          
class ContactMsg(db.Model):
    __tablename__ = 'contactmsg'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    message = db.Column(db.Text)

    def __repr__(self):
        return f"ContactMsg('{self.name}','{self.email}','{self.subject}'\
                      '{self.message}')"