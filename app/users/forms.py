from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField, 
                     SelectField, DateField, RadioField, TextAreaField, IntegerField)
from wtforms.validators import (DataRequired, Optional, Length, Email, EqualTo, 
                                ValidationError, NoneOf)
from flask_login import current_user
from app.models.usermodel import User
import pycountry


# Create a login form class
class LoginForm(FlaskForm):
    '''This class enable to model the login forms'''
    # Difining some data field with necessary validators
    #username = StringField('Username', validators=[DataRequired(), Length(min=5, max=15)]) 
    email = StringField('Email address', validators=[DataRequired(), Email()]) 
    password =  PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Sign In')


# Create a registration form class
class RegistrationForm(FlaskForm):
    '''This class enable to model the registration forms'''
    # Personal details
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=40)])
    last_name = StringField('Surname', validators=[DataRequired(), Length(max=40)])
    #gender = SelectField("Gender", choices=[(' ', ' '), ('Male', 'Male'), ('Female', 'Female')])
    dob = DateField('Date of birth', validators=[DataRequired()])
    
    # Contact info
    #company_name =  StringField('Company Name ', validators=[Length(min=3, max=30)])
    #address = StringField('Addresse', validators=[Length(max=100)])
    #city =  StringField('City', validators=[Length(min=2, max=40)])
    #zip_code =  StringField('Zip code ', validators=[Length(min=2, max=10)])
    #country = SelectField('Country', choices = [(country.alpha_2, country.name) for country in pycountry.countries])
    #phone = StringField('Phone number', validators=[Length(max=30)])
    
    # Connection info
    username = StringField('Username', validators=[DataRequired(), Length(min=5, max=20)]) 
    email = StringField('Email', validators=[DataRequired(), Length(max=100), Email()]) 
    password =  PasswordField('Password', validators=[DataRequired(), Length(min=8, max=20)])
    confirm_password =  PasswordField('Retype password', validators=[DataRequired(), EqualTo('password')])
    terms = RadioField('Accept T&C', choices=[('Yes','Yes'), ('No', 'No')],  validators=[DataRequired()], default='Yes' )
    #role = StringField('Role', validators=[DataRequired(), Length(max=20)], default='member')
    submit = SubmitField('Sign Up')

    # defining a form validation function for username
    def validate_username(self, username):
        '''This function validate the user username'''
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.') 
    # defining a form validation function for email
    def validate_email(self, email):
        '''This function validate the user email'''
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken!. Please choose a different one.') 