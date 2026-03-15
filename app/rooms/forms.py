from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField, FloatField, 
                     SelectField, DateField, RadioField, TextAreaField, IntegerField,
                     SelectMultipleField)
#from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import (DataRequired, Optional, Length, Email, EqualTo, 
                                ValidationError, NoneOf)
from flask_login import current_user
from app.models.usermodel import User 
from app.models.roommodel import Rooms, Roomextra
#import pycountry

# class MultiCheckboxField(SelectMultipleField):
# 	widget		  = ListWidget(prefix_label=False)
# 	option_widget = CheckboxInput()

# Create a room listing form class 
class AddRoomForm(FlaskForm):
    '''This class enable to model the room listing process'''
    # Defining some fields that can be updated with necessary validators
    room_name =  StringField('', validators=[DataRequired(), Length(min=5, max=30)])
    room_location =  StringField('', validators=[DataRequired(), Length(max=30)])
    room_category = SelectField('',choices=[(' ', ' '), ('Single Room', 'Single Room'), ('Double Room', 'Double Room'), 
                               ('Twin Room', 'Twin Room'), ('Family Room', 'Family Room')], validators=[DataRequired()])
    short_desc = StringField('', validators=[DataRequired(), Length(min=10, max=50)]) 
    room_size = SelectField('',choices=[(' ', ' '), ('14–23', '14–23'), ('20–35', '20–35'), 
                               ('30–45', '30–45'), ('40–60', '40–60')], validators=[DataRequired()]) 
    max_occupancy = SelectField('', choices=[(' ', ' '), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), 
                                              ('5', '5')], validators=[DataRequired()])
    price = FloatField('', validators=[DataRequired()])
    description = TextAreaField('', validators=[DataRequired(), Length(min=100, max=350)])
    status =  SelectField('', choices=[(' ', ' '), ('Occupied', 'Occupied'), ('Available', 'Available')], 
                                validators=[DataRequired()])
    #services = MultiCheckboxField('', choices=[('Resto','Resto'), ('Bar','Bar'),
    #                                          ('Spa','Spa'), ('Shopping','Shopping')])
    #amenities = MultiCheckboxField('', choices=[('Tv','Tv'), ('Hot water','Hot water'),
    #                                          ('Double bed','Double bed'), ('Towels','Towels')])

    submit = SubmitField('Submit')

# Create a room service et amenities form class 
class RoomExtraForm(FlaskForm):
    '''This class enable to model the room extra process'''
    # Room amenities
    sleeping = SelectField('', choices=[('Double', 'Double'), 
                                ('Single', 'Single'), ('King', 'King')], 
                                validators=[DataRequired()], default='Single')
    hot_water = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')],
                                validators=[DataRequired()], default='No') 
    tv = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')], 
                                 validators=[DataRequired()], default='No') 
    internet = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')], 
                                 validators=[DataRequired()], default='No')
    kitchen = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')], 
                                 validators=[DataRequired()], default='No')
    towels = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()], default='Yes')
    # Room Services
    resto = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()], default='No')
    bar = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')],
                                validators=[DataRequired()], default='No') 
    spa = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()], default='No') 
    shop = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()], default='No')
    concierge = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()], default='No')
    car = SelectField('', choices=[('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()], default='No')
                                              
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
    #max_occupancy = SelectField('',choices=[(' ', ' '), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), 
    #                                          ('5', '5')], validators=[DataRequired()])
    max_occupancy = IntegerField('', validators=[DataRequired()])
    price = FloatField('', validators=[DataRequired()])
    description = TextAreaField('', validators=[DataRequired(), Length(min=100, max=350)])
    status =  SelectField('', choices=[(' ', ' '), ('Occupied', 'Occupied'), ('Available', 'Available')], 
                        validators=[DataRequired()])
    submit = SubmitField('Update')


# Update room picture form class 
class UpdateRoomPictureForm(FlaskForm):
    '''This class enable to model the room picture update process'''
    picture1 = FileField('Upload image 1', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    picture2 = FileField('Upload image 2', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    picture3 = FileField('Upload image 3', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    picture4 = FileField('Upload image 4', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    picture5 = FileField('Upload image 5', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    picture6 = FileField('Upload image 6', validators=[FileAllowed(['jpg', 'jpeg', 'png'])] )
    submit = SubmitField('Update')