from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin, current_user
from flask import current_app, render_template
from itsdangerous import URLSafeTimedSerializer as Serializer


# defining a function decorator that fectch the user by id 
# callback to reload the user object 
@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))

# Creating the user db model
class User(db.Model, UserMixin):
    '''This class is a User model'''
    # adding the columns
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Personal detail
    first_name = db.Column(db.String(40), nullable=False)
    last_name = db.Column(db.String(40), nullable=False)
    gender = db.Column(db.String, nullable=True, default='Change me')
    dob = db.Column(db.Date, nullable=False)
    # Location
    address = db.Column(db.String(100), nullable=True, default='Change me')
    city = db.Column(db.String(40), nullable=True, default='Change me')
    zip_code = db.Column(db.String(10), nullable=True, default='Change me')
    country = db.Column(db.String(40), nullable=True, default='Change me')
    #Contact info
    company_name = db.Column(db.String(30), nullable=True, default='Change me')
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    phone = db.Column(db.String(30), nullable=True, default='Change me')
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    terms = db.Column(db.String(5), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member') # member / admin
    aboutme = db.Column(db.String(150), nullable=True, default='Tell the word something nice about yourself')
    # posts = db.relationship('Post', backref='author', lazy=True)

    # REsetting a web signature token
    def get_reset_token(self, max_age=1800):
        '''This function generate Token'''
        s = Serializer(current_app.config['SECRET_KEY'])
        token = s.dumps({'user_id': self.id}) #.decode('utf-8')
        return token

    @staticmethod
    def verify_reset_token(token):
        '''This function validate password resset Token'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=1800)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
    def __repr__(self):
        return f"User('{self.first_name}','{self.last_name}','{self.gender}','{self.dob}'\
                      '{self.address}','{self.city}','{self.zip_code}','{self.country}'\
                      '{self.company_name}, {self.phone}','{self.username}','{self.email}'\
                      '{self.image_file}', {self.terms}','{self.role}', '{self.aboutme}')"  