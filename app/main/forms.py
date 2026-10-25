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
    # limits match the ContactMsg columns (100) and keep one message from
    # being an unbounded email to the inbox
    name = StringField("", validators=[DataRequired(), Length(max=100)])
    email = EmailField("", validators=[DataRequired(), Email(), Length(max=100)])
    subject = StringField( "", validators=[DataRequired(), Length(max=100)])
    message = TextAreaField("", validators=[DataRequired(), Length(max=2000)])

    submit = SubmitField("Send")