from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField, FloatField, 
                     SelectField, DateField, RadioField, TextAreaField, IntegerField)
from wtforms.validators import (DataRequired, Optional, Length, Email, EqualTo, 
                                ValidationError, NoneOf)
from flask_login import current_user
from app.models.usermodel import User 
from app.models.roommodel import Rooms
#import pycountry


# Create a room listing form class 
class AddRoomForm(FlaskForm):
    '''This class enable to model the room listing process'''
    # Defining some fields that can be updated with necessary validators
    room_name =  StringField('', validators=[DataRequired(), Length(min=5, max=30)])
    room_location =  StringField('', validators=[DataRequired(), Length(max=30)])
    room_category = SelectField('',choices=[(' ', ' '), ('Single Room', 'Single Room'), ('Double Room', 'Double Room'), 
                               ('Twin Room', 'Twin Room'), ('Family Room', 'Family Room')], validators=[DataRequired()])
    short_desc = StringField('', validators=[DataRequired(), Length(min=10, max=100)]) 
    room_size = SelectField('',choices=[(' ', ' '), ('14–23', '14–23'), ('20–35', '20–35'), 
                               ('30–45', '30–45'), ('40–60', '40–60')], validators=[DataRequired()]) 
    max_occupancy = SelectField('', choices=[(' ', ' '), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), 
                                              ('5', '5')], validators=[DataRequired()])
    price = FloatField('', validators=[DataRequired()])
    description = TextAreaField('', validators=[DataRequired(), Length(min=100, max=350)])
    status =  SelectField('', choices=[(' ', ' '), ('Occupied', 'Occupied'), ('Available', 'Available')], 
                                validators=[DataRequired()])
    picture1 = FileField('', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    picture2 = FileField('', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    picture3 = FileField('', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    submit = SubmitField('Submit')

# Create a room listing update form class 
class UpdateRoomForm(FlaskForm):
    '''This class enable to model the room listing update process'''
    # Defining some fields that can be updated with necessary validators
    room_name =  StringField('', validators=[DataRequired(), Length(min=5, max=30)])
    #room_location =  StringField('', validators=[DataRequired(), Length(max=30)])
    room_category = SelectField('',choices=[(' ', ' '), ('Single Room', 'Single Room'), ('Double Room', 'Double Room'), 
                               ('Twin Room', 'Twin Room'), ('Family Room', 'Family Room')], validators=[DataRequired()])
    short_desc = StringField('', validators=[DataRequired(), Length(min=10, max=100)]) 
    #room_size = SelectField('',choices=[(' ', ' '), ('14–23', '14–23'), ('20–35', '20–35'), 
    #                          ('30–45', '30–45'), ('40–60', '40–60')], validators=[DataRequired()]) 
    max_occupancy = SelectField('', choices=[(' ', ' '), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), 
                                              ('5', '5')], validators=[DataRequired()])
    price = FloatField('', validators=[DataRequired()])
    description = TextAreaField('', validators=[DataRequired(), Length(min=100, max=350)])
    status =  SelectField('', choices=[(' ', ' '), ('Occupied', 'Occupied'), ('Available', 'Available')], 
                                validators=[DataRequired()])
    picture1 = FileField('', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    picture2 = FileField('', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    picture3 = FileField('', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    submit = SubmitField('Submit')