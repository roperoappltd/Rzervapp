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
from app.models.roommodel import Rooms, Roomextra, Roomreviews
from app.models.bookmodel import Bookings, Vouchers
from datetime import date
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
    price = IntegerField('', validators=[DataRequired()])
    description = TextAreaField('', validators=[DataRequired(), Length(min=100, max=350)])
    status =  SelectField('', choices=[(' ', ' '), ('Occupied', 'Occupied'), ('Available', 'Available')], 
                                validators=[DataRequired()])
    usp1 =  StringField('', validators=[Length(min=5, max=20)])
    usp2 =  StringField('', validators=[Length(min=5, max=20)])
    usp3 =  StringField('', validators=[Length(min=5, max=20)])
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
    price = IntegerField('', validators=[DataRequired()])
    description = TextAreaField('', validators=[DataRequired(), Length(min=100, max=350)])
    status =  SelectField('', choices=[(' ', ' '), ('Occupied', 'Occupied'), ('Available', 'Available')], 
                        validators=[DataRequired()])
    usp1 =  StringField('', validators=[Length(min=5, max=20)])
    usp2 =  StringField('', validators=[Length(min=5, max=20)])
    usp3 =  StringField('', validators=[Length(min=5, max=20)])

    submit = SubmitField('Update')


# Update room picture form class 
class UpdateRoomPictureForm(FlaskForm):
    '''This class enable to model the room picture update process'''
    picture1 = FileField('Image 1', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])] )
    picture2 = FileField('Image 2', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])] )
    picture3 = FileField('Image 3', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])] )
    picture4 = FileField('Image 4', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])] )
    picture5 = FileField('Image 5', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])] )
    picture6 = FileField('Image 6', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])] )
    submit = SubmitField('Update')

# Create an review form class
class RoomReviewsForm(FlaskForm):
    '''This class enable to generate Room reviews form'''
    # Define the field and the validators
    rate_us = SelectField('', choices=[(' ', ' '), ('1', '1'), ('2', '2'), ('3', '3'),
                                         ('4', '4'), ('5', '5')], validators=[DataRequired()]) 
    message = TextAreaField('', validators=[DataRequired(), Length(min=20, max=200)])
    submit = SubmitField('Send')

# ============================================================== BOOKING
# Create a booking form class
class BookingForm(FlaskForm):
    '''This class enable to generate room booking form'''
    # Define the field and the validators
    arrival = DateField('Arrival Date', validators=[DataRequired()])
    departure = DateField('Departure Date', validators=[DataRequired()])
    num_guests = StringField('Total Guest', validators=[DataRequired()])
    #num_rooms = SelectField('', choices=[(' ', ' '), ('1', '1'), ('2', '2'), ('3', '3'),('4', '4'), 
    #                                     ('5', '5')], validators=[DataRequired()]) 
    room_type = SelectField('Room category',choices=[(' ', ' '), ('Single Room', 'Single Room'), ('Double Room', 'Double Room'), 
                               ('Twin Room', 'Twin Room'), ('Family Room', 'Family Room')], validators=[DataRequired()])
    ad_info = TextAreaField('Additional Information', default="What would you like?")
    primary_guest = StringField('', validators=[DataRequired()])
    pguest_email = StringField('', validators=[DataRequired()])
    pguest_phone = StringField('', validators=[DataRequired()])
    submit = SubmitField('Proceed to checkout')

    def validate_arrival(self, arrival):
        if arrival.data < date.today():
            raise ValidationError('Arrival must be today or later.')

    def validate_departure(self, departure):
        if departure.data < self.arrival.data:
            raise ValidationError('Departure must be after Arrival.')

# Create an payments form class
class PaymentForm(FlaskForm):
    '''This class enable to generate payment form'''
    # Define the field and the validators
    pay_method = RadioField('Select a payment option: ', choices=[('Debit/Credit Card',
                            'Debit/Credit Card'), ('Paypal', 'Paypal'), ('Cash on Arrival', 'Cash on Arrival')],  
                            validators=[DataRequired()])
    #amount_paid = IntegerField('', validators=[DataRequired()])
    #discount = IntegerField('', validators=[DataRequired()], default=0.00)
    #serv_charge = IntegerField('', validators=[DataRequired()], default=0.00)
    #rzerv_points = IntegerField('', validators=[DataRequired()], default=20)
    submit = SubmitField('Checkout now!')

class VouchersForm(FlaskForm):
    '''This class enable to generate voucher form'''
    # Define the field and the validators
    code = StringField('Enter a voucher code: ')
    submit = SubmitField('Redeem')

    def validate_code(self, code):
        voucher = Vouchers.query.filter_by(code=code.data).first()
        if not voucher:
            raise ValidationError('Invalid voucher code.')
        else:
            raise ValidationError(f'£{voucher.value} discount has been applied!')