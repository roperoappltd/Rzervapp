from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, SubmitField, BooleanField, FloatField, 
                     SelectField, DateField, TextAreaField, IntegerField,
                     EmailField, HiddenField)
from app import db
from wtforms.validators import (DataRequired, Optional, Length, Email, EqualTo, 
                                ValidationError, NoneOf)
from flask_login import current_user


class ContactForm(FlaskForm):
    name = StringField("", validators=[DataRequired()])
    email = EmailField("", validators=[DataRequired(), Email()])
    subject = StringField( "", validators=[DataRequired()])
    message = TextAreaField("", validators=[DataRequired()])

    submit = SubmitField("Send")