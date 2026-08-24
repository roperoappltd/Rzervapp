from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField, FloatField, 
                     SelectField, DateField, TextAreaField, IntegerField,
                     MultipleFileField, HiddenField)
from app import db
#from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import (DataRequired, Optional, Length, Email, EqualTo, 
                                ValidationError, NumberRange, NoneOf)
from flask_login import current_user
from app.models.usermodel import User 
from app.models.roommodel import Rooms, Roomextra, Roomreviews
from app.models.bookmodel import Bookings, Vouchers
from datetime import date
#import pycountry

# Create a room listing form class 
class AddRoomForm(FlaskForm):
    '''This class enable to model the room listing process'''
    # Defining some fields that can be updated with necessary validators
    room_name =  StringField('', validators=[DataRequired(), Length(min=5, max=30)])
    room_location =  StringField('', validators=[DataRequired(), Length(max=30)])
    borough = StringField('', validators=[DataRequired(), Length(max=50)])
    room_category = SelectField('',choices=[('', ' '), ('Single Room', 'Single Room'), ('Double Room', 'Double Room'), 
                               ('Twin Room', 'Twin Room'), ('Family Room', 'Family Room')], validators=[DataRequired()])
    short_desc = StringField('', validators=[DataRequired(), Length(min=10, max=50)]) 
    room_size = SelectField('',choices=[('', ' '), ('14–23', '14–23'), ('20–35', '20–35'), 
                               ('30–45', '30–45'), ('40–60', '40–60')], validators=[DataRequired()]) 
    max_occupancy = SelectField('', choices=[('', ' '), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), 
                                              ('5', '5')], validators=[DataRequired()])
    price = FloatField('', validators=[DataRequired()])
    description = TextAreaField('', validators=[DataRequired(), Length(min=100, max=350)])
    status =  SelectField('', choices=[('', ' '), ('Available', 'Available'),('Maintenance', 'Maintenance'),], 
                                validators=[DataRequired()])
    rule1 =  StringField('', validators=[Optional(), Length(min=5, max=60)])
    rule2 =  StringField('', validators=[Optional(), Length(min=5, max=60)])
    rule3 =  StringField('', validators=[Optional(), Length(min=5, max=60)])
    # discount_percent = IntegerField('', validators=[Optional(), NumberRange(min=0, max=90)])
    discount_percent = SelectField('',choices=[('', ' '), ('10', '10'), ('15', '15'), ('20', '20'),('25', '25'),
                                        ('30', '30'), ('35', '35')], validators=[Optional()]) 
    
    submit = SubmitField('Submit')

# Create a room service et amenities form class 
class RoomExtraForm(FlaskForm):
    '''This class enable to model the room extra process'''
    # Room amenities
    sleeping = SelectField('', choices=[('',''), ('Double', 'Double'), 
                                ('Single', 'Single'), ('King', 'King')], 
                                validators=[DataRequired()])
    hot_water = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')],
                                validators=[DataRequired()]) 
    smart_tv = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], 
                                 validators=[DataRequired()]) 
    internet = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], 
                                 validators=[DataRequired()])
    kitchen = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], 
                                 validators=[DataRequired()])
    towels = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()])
    # Room Services
    resto = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()])
    bar = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')],
                                validators=[DataRequired()]) 
    spa = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()]) 
    shop = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()])
    concierge = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()])
    car = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], 
                                validators=[DataRequired()])
    # confort & Leisure
    aircon = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    pool = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    workspace = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    washing = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    sport = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    parking = SelectField('', choices=[('',''), ('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
                                              
    submit = SubmitField('Submit')


# Create a room listing update form class 
class UpdateRoomForm(FlaskForm):
    '''This class enable to model the room listing update process'''
    # Defining some fields that can be updated with necessary validators
    room_name =  StringField('', validators=[DataRequired(), Length(min=5, max=30)])
    #room_location =  StringField('', validators=[DataRequired(), Length(max=30)])
    #borough = StringField('', validators=[DataRequired(), Length(max=50)])  
    # LOCKED: same reasoning as room_location -- a room's physical location, 
    # at any granularity, doesn't change post-creation. Genuine typo correction 
    # goes through RoomAdmin instead, not routine self-service editing.
    room_category = SelectField('',choices=[('', ' '), ('Single Room', 'Single Room'), ('Double Room', 'Double Room'), 
                               ('Twin Room', 'Twin Room'), ('Family Room', 'Family Room')], validators=[DataRequired()])
    short_desc = StringField('', validators=[DataRequired(), Length(min=10, max=100)]) 
    #room_size = SelectField('',choices=[(' ', ' '), ('14–23', '14–23'), ('20–35', '20–35'), 
    #                          ('30–45', '30–45'), ('40–60', '40–60')], validators=[DataRequired()]) 
    #max_occupancy = SelectField('',choices=[(' ', ' '), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), 
    #                                          ('5', '5')], validators=[DataRequired()])
    max_occupancy = IntegerField('', validators=[DataRequired()])
    price = FloatField('', validators=[DataRequired()])  # FIXED: was missing DataRequired -- model has nullable=False + CHECK price > 0, an empty submission would throw IntegrityError
    description = TextAreaField('', validators=[DataRequired()])
    status =  SelectField('', choices=[('', ' '), ('Maintenance', 'Maintenance'), ('Available', 'Available'),
                                      ('Hidden', 'Hidden'), ('Inactive', 'Inactive')],validators=[DataRequired()])
    rule1 =  StringField('', validators=[Optional(), Length(min=10, max=60)] )
    rule2 =  StringField('', validators=[Optional(), Length(min=10, max=60)] ) 
    rule3 =  StringField('', validators=[Optional(), Length(min=10, max=60)] )
    # discount_percent = IntegerField('', validators=[Optional(), NumberRange(min=0, max=90)])
    discount_percent = SelectField('',choices=[('', ' '), ('10', '10'), ('15', '15'), ('20', '20'),('25', '25'),
                                            ('30', '30'), ('35', '35')], validators=[Optional()]) 
    
    submit = SubmitField('Update')

# Update room picture form class 
class UpdateRoomPictureForm(FlaskForm):
    '''One optional field per image slot -- lets a host replace any
    subset of the 6 images without touching the others. Previously a
    single MultipleFileField with no way to target a specific slot,
    which combined with the route always wiping all 6 first, meant any
    partial update destroyed the untouched images.'''
    image1 = FileField('Image 1', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')])
    image2 = FileField('Image 2', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')])
    image3 = FileField('Image 3', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')])
    image4 = FileField('Image 4', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')])
    image5 = FileField('Image 5', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')])
    image6 = FileField('Image 6', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')])
    submit = SubmitField('Update')

# Create an review form class
class RoomReviewsForm(FlaskForm):
    '''This class enable to generate Room reviews form'''
    # Define the field and the validators
    rate_us = SelectField('', choices=[('', ' '), ('1', '1'), ('2', '2'), ('3', '3'),
                                         ('4', '4'), ('5', '5')], validators=[DataRequired()])  # FIXED: placeholder value was ' ' (a space, truthy) -- now '' (reliably falsy across WTForms versions)
    message = TextAreaField('', validators=[DataRequired(), Length(min=20, max=200)])
    submit = SubmitField('Send')

class GuestReviewForm(FlaskForm):
    '''Mirrors RoomReviewsForm exactly, for UI/UX consistency between
    room reviews and guest reviews.'''
    rate_us = SelectField('', choices=[('', ' '), ('1', '1'), ('2', '2'), ('3', '3'),
                                         ('4', '4'), ('5', '5')], validators=[DataRequired()])
    message = TextAreaField('', validators=[DataRequired(), Length(min=20, max=200)])
    submit = SubmitField('Send')

# ============================================================== BOOKING
# Create a booking form class
class BookingForm(FlaskForm):
    '''This class enable to generate room booking form'''
    # Define the field and the validators
    arrival = DateField('', validators=[DataRequired()])
    departure = DateField('', validators=[DataRequired()])
    num_guests = StringField('', validators=[DataRequired()])
    room_type = SelectField('',choices=[(' ', ' '), ('Single Room', 'Single Room'), ('Double Room', 'Double Room'), 
                               ('Twin Room', 'Twin Room'), ('Family Room', 'Family Room')], validators=[DataRequired()])
    ad_info = TextAreaField('', default="What would you like?")
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
    #vcode = HiddenField()
    # pay_method removed -- was a cosmetic radio selector (Card/Paypal/
    # Cash) that never drove any real logic even before Paystack, and
    # would now be actively misleading (e.g. offering "Paypal" when
    # Paystack doesn't support it). The real payment method choice
    # happens on Paystack's own checkout page after redirect.
    voucher_code =  StringField('Enter a voucher code (Optional): ', validators=[Optional()])
    submit = SubmitField('')
    # def validate_code(self, code):
    #     # empty voucher allowed
    #     if not code.data:
    #         return
    #     # retrieve session value
    #     voucher = Vouchers.query.filter_by(code=code.data, is_active='True').first()
    #     if not voucher:
    #         raise ValidationError(
    #             "Invalid or inactive voucher code."
    #         )

class VouchersForm(FlaskForm):
    '''This class enable to generate voucher form'''
    # Define the field and the validators
    code = StringField('Enter a voucher code: ')
    #value = HiddenField()
    submit = SubmitField('Redeem')

    def validate_code(self, code):
        voucher = Vouchers.query.filter_by(code=code.data).first()
        if not voucher:
            raise ValidationError('Invalid voucher code.')
        else:
            raise ValidationError(f'£{voucher.value} discount has been applied!')

class RoomSearchForm(FlaskForm):
    room_location = SelectField('', choices = [ ], validators=[Optional()])
    borough = SelectField('', choices = [ ], validators=[Optional()])
    room_category = SelectField('', choices = [ ], validators=[Optional()])
    min_price = FloatField('', validators=[Optional()])
    max_price = FloatField('', validators=[Optional()])
    submit = SubmitField("Apply Filters")

class CancelBookingForm(FlaskForm):
    submit = SubmitField("Cancel")

class WithdrawalForm(FlaskForm):
    amount = FloatField("Amount",validators=[DataRequired(), NumberRange(min=10)])
    submit = SubmitField("Request")