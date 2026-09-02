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
    username = StringField('Username', validators=[DataRequired(), Length(min=5, max=20)]) 
    dob = DateField('Date of birth', validators=[DataRequired(), User.validate_dob_minimum_age])
    country = SelectField('Country', validators=[DataRequired()],
                          choices=[('', 'Select your country')] + [(country.alpha_2, country.name) for country in pycountry.countries])
    gender = SelectField('Gender', choices=[(' ', ' '), ('Male', 'Male'), ('Female', 'Female')])
    # Connection info
    email = StringField('Email', validators=[DataRequired(), Length(max=100), Email(), Length(max=100)]) 
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])  # FIXED: was max=20, an OWASP-flagged anti-pattern that blocks strong/password-manager-generated passwords
    confirm_password =  PasswordField('Retype password', validators=[DataRequired(), EqualTo('password')])
    terms = BooleanField('I accept the Terms & Conditions', validators=[DataRequired()])  # FIXED: was a Yes/No RadioField returning a string -- 'No' is truthy in Python, a real fail-open risk if ever naively coerced to bool
    submit = SubmitField('Sign Up')

    # defining a form validation function for username
    def validate_username(self, username):
        '''This function validate the user username'''
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is taken. Please change.') 
    # defining a form validation function for email
    def validate_email(self, email):
        '''This function validate the user email'''
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken!. Please choose a different one.')

# Create an update account form class
class UpdateAccountForm(FlaskForm):
    '''This class enable to model the user account update forms'''
    # Defining some field that can be updated with necessary validators
    company_name =  StringField('', validators=[Length(min=3, max=30)])
    username = StringField('', validators=[DataRequired(), Length(min=5, max=15)]) 
    email = StringField('', validators=[DataRequired(), Email()]) 
    #first_name = StringField('', validators=[DataRequired(), Length(max=40)])
    #last_name = StringField('', validators=[DataRequired(), Length(max=40)])
    gender = SelectField('', choices=[(' ', ' '), ('Male', 'Male'), ('Female', 'Female')])
    phone = StringField('', validators=[Length(max=30)])
    address = StringField('', validators=[Length(max=100)])
    city =  StringField('', validators=[Length(min=2, max=40)])
    country = SelectField('', choices = [(country.alpha_2, country.name) for country in pycountry.countries])
    zip_code =  StringField('', validators=[Length(min=2, max=10)])
    aboutme = TextAreaField('', validators=[DataRequired(), Length(min=30, max=200)])
    #Enabling profile picture update and allowed image extensions
    picture = FileField('Upload profile picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    submit = SubmitField('Update')

    # defining a form validation function for username
    def validate_username(self, username):
        '''This function validate the user username if username update different from the previous'''
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username is taken. Please change.') 
        
    # defining a form validation function for email
    def validate_email(self, email):
        '''This function validate the user Email if the email update from previous'''
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email is taken!. Please change.') 

# Create a form to request password reset form
class ResendVerificationForm(FlaskForm):
    '''Form for requesting a fresh email-verification link. Deliberately
    has no custom validator checking whether the email exists (unlike
    RequestResetForm below) -- the route itself shows the same generic
    message regardless, so this form can't be used to enumerate which
    emails are registered on the site.'''
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Resend Verification Email')

class RequestResetForm(FlaskForm):
    '''This class enable to generate request password reset form'''
    email = StringField('Email', validators=[DataRequired(), Email()])  
    submit = SubmitField('Request Password Reset')
     # defining a form validation function for email
    def validate_email(self, email):
        '''This function validate the user email'''
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('No account with that email. Please, Register Now!') 

# Create a reset password form 
class ResetPasswordForm(FlaskForm):
    '''This class enable to generate password reset form'''
    password =  PasswordField('Password', validators=[DataRequired(), Length(min=8, max=20)])
    confirm_password =  PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Password Reset')

class DeleteAccountForm(FlaskForm):
    '''Requires re-entering the password, same principle as most real
    platforms gating irreversible account actions -- a single click on a
    page someone's already logged into isn't enough friction for
    something this permanent.'''
    password = PasswordField('Confirm your password', validators=[DataRequired()])
    submit = SubmitField('Permanently delete my account')