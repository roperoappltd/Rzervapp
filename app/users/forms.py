from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField, 
                     SelectField, DateField, RadioField, TextAreaField, IntegerField)
from wtforms.validators import (DataRequired, Optional, Length, Email, EqualTo, 
                                ValidationError, NoneOf, Regexp)
from flask_login import current_user
from flask_babel import gettext as _, lazy_gettext as _l, get_locale
from app.models.usermodel import User
import gettext as _pygettext
import unicodedata
import pycountry
import re


# SECURITY: usernames are shown in chat, notifications and review pop-ups,
# so they are restricted to a safe character set instead of free text.
USERNAME_PATTERN = r'^[A-Za-z0-9_.\-]+\Z'


def _country_choices():
    '''Country dropdown choices, names translated into the visitor's language.
    pycountry ships ISO 3166 translations; falls back to the English name when a
    language has none. Built per request (not at import time) so it follows the
    language the visitor picked. Stored values stay the alpha_2 codes.'''
    lang = str(get_locale() or 'en')
    try:
        translate = _pygettext.translation('iso3166-1', pycountry.LOCALES_DIR,
                                           languages=[lang]).gettext
    except OSError:
        translate = lambda name: name

    def sort_key(item):  # accent-insensitive so "Égypte" sorts under E
        return unicodedata.normalize('NFKD', item[1]).encode('ascii', 'ignore').decode().lower()

    countries = sorted(((c.alpha_2, translate(c.name)) for c in pycountry.countries), key=sort_key)
    return [('', _('Select your country'))] + countries


# Create a login form class
class LoginForm(FlaskForm):
    '''This class enable to model the login forms'''
    # Difining some data field with necessary validators
    #username = StringField('Username', validators=[DataRequired(), Length(min=5, max=15)]) 
    email = StringField(_l('Email address'), validators=[DataRequired(), Email()]) 
    password =  PasswordField(_l('Password'), validators=[DataRequired()])
    remember = BooleanField(_l('Remember me'))
    submit = SubmitField(_l('Sign In'))

# Create a registration form class
class RegistrationForm(FlaskForm):
    '''This class enable to model the registration forms'''
    # Personal details
    first_name = StringField(_l('First Name'), validators=[DataRequired(), Length(max=40)])
    last_name = StringField(_l('Surname'), validators=[DataRequired(), Length(max=40)])
    #gender = SelectField("Gender", choices=[(' ', ' '), ('Male', 'Male'), ('Female', 'Female')])
    username = StringField(_l('Username'), render_kw={'maxlength': 9}, validators=[DataRequired(), Length(min=5, max=9),
                           Regexp(USERNAME_PATTERN, message=_l('Username can only contain letters, numbers, dots, dashes and underscores.'))]) 
    dob = DateField(_l('Date of birth'), validators=[DataRequired(), User.validate_dob_minimum_age])
    # choices are filled in __init__ below so the names follow the visitor's language
    country = SelectField(_l('Country'), validators=[DataRequired()], choices=[])
    gender = SelectField(_l('Gender'), choices=[(' ', ' '), ('Male', _l('Male')), ('Female', _l('Female'))])
    # Connection info
    email = StringField(_l('Email'), validators=[DataRequired(), Length(max=100), Email(), Length(max=100)]) 
    password = PasswordField(_l('Password'), validators=[DataRequired(), Length(min=8, max=128)])  # FIXED: was max=20, an OWASP-flagged anti-pattern that blocks strong/password-manager-generated passwords
    confirm_password =  PasswordField(_l('Retype password'), validators=[DataRequired(), EqualTo('password', message=_l('Passwords do not match.'))])
    terms = BooleanField(_l('I accept the Terms & Conditions'), validators=[DataRequired()])  # FIXED: was a Yes/No RadioField returning a string -- 'No' is truthy in Python, a real fail-open risk if ever naively coerced to bool
    submit = SubmitField(_l('Sign Up'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country.choices = _country_choices()

    # defining a form validation function for username
    def validate_username(self, username):
        '''This function validate the user username'''
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(_('Username is taken. Please change.'))
    # defining a form validation function for email
    def validate_email(self, email):
        '''This function validate the user email'''
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(_('That email is taken!. Please choose a different one.'))

# Create an update account form class
class UpdateAccountForm(FlaskForm):
    '''This class enable to model the user account update forms'''
    # Defining some field that can be updated with necessary validators
    company_name =  StringField('', validators=[Length(min=3, max=30)])
    # Length is checked in validate_username() below, and only when the name
    # is actually changed, so older accounts with longer names can still save
    # the rest of their profile.
    username = StringField('', validators=[DataRequired()]) 
    email = StringField('', validators=[DataRequired(), Email()]) 
    #first_name = StringField('', validators=[DataRequired(), Length(max=40)])
    #last_name = StringField('', validators=[DataRequired(), Length(max=40)])
    gender = SelectField('', choices=[(' ', ' '), ('Male', _l('Male')), ('Female', _l('Female'))])
    phone = StringField('', validators=[Length(max=30)])
    address = StringField('', validators=[Length(max=100)])
    city =  StringField('', validators=[Length(min=2, max=40)])
    country = SelectField('', choices = [(country.alpha_2, country.name) for country in pycountry.countries])
    zip_code =  StringField('', validators=[Length(min=2, max=10)])
    aboutme = TextAreaField('', validators=[DataRequired(), Length(min=30, max=200)])
    #Enabling profile picture update and allowed image extensions
    picture = FileField(_l('Upload profile picture'), validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    submit = SubmitField(_l('Update'))

    # defining a form validation function for username
    def validate_username(self, username):
        '''This function validate the user username if username update different from the previous'''
        if username.data != current_user.username:
            # Only enforced when the username actually changes, so existing
            # accounts with an older username can still save other fields.
            if not 5 <= len(username.data or '') <= 9:
                raise ValidationError(_('Username must be between 5 and 9 characters long.'))
            if not re.match(USERNAME_PATTERN, username.data or ''):
                raise ValidationError(_('Username can only contain letters, numbers, dots, dashes and underscores.'))
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(_('Username is taken. Please change.'))
        
    # defining a form validation function for email
    def validate_email(self, email):
        '''This function validate the user Email if the email update from previous'''
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(_('Email is taken!. Please change.'))

# Create a form to request password reset form
class ResendVerificationForm(FlaskForm):
    '''Form for requesting a fresh email-verification link. Deliberately
    has no custom validator checking whether the email exists (unlike
    RequestResetForm below) -- the route itself shows the same generic
    message regardless, so this form can't be used to enumerate which
    emails are registered on the site.'''
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Resend Verification Email'))

class RequestResetForm(FlaskForm):
    '''This class enable to generate request password reset form'''
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))
    # SECURITY: deliberately NO check that the email has an account. The
    # old validator ("No account with that email") let anyone test which
    # addresses are registered. The route answers the same either way.

# Create a reset password form 
class ResetPasswordForm(FlaskForm):
    '''This class enable to generate password reset form'''
    password =  PasswordField(_l('Password'), validators=[DataRequired(), Length(min=8, max=20)])
    confirm_password =  PasswordField(_l('Confirm Password'), validators=[DataRequired(), EqualTo('password', message=_l('Passwords do not match.'))])
    submit = SubmitField(_l('Password Reset'))

class DeleteAccountForm(FlaskForm):
    '''Requires re-entering the password, same principle as most real
    platforms gating irreversible account actions -- a single click on a
    page someone's already logged into isn't enough friction for
    something this permanent.'''
    password = PasswordField(_l('Confirm your password'), validators=[DataRequired()])
    submit = SubmitField(_l('Permanently delete my account'))