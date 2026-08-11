import logging
import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_login import current_user
from flask_mail import Message
from app import mail
import cv2
import bleach
from datetime import *



# Create a function that handle profile picture
def save_picture(form_picture):
    '''This function add random hex byte & extension to a file a save to a location '''
    # create a random hex of 4 bytes
    random_hex = secrets.token_hex(4)
    # slice the file name and file extension of the picture update
    _, file_ext = os.path.splitext(form_picture.filename)
    # combine the random hex with the file extension in order set the name of the new uploaded file
    uploaded_PicName = f'{current_user.username}' + random_hex + file_ext 
    # extract and define the path where to save the file
    picture_path = os.path.join(current_app.root_path, 'static/userpics/roompics/', uploaded_PicName)
    # Resizing the  picture before saving
    img_sizer = (960, 640)
    new_img = Image.open(form_picture)
    new_img.thumbnail(img_sizer) # 
    # Saving the picture
    new_img.save(picture_path)
    return uploaded_PicName

def list_sum(lst):
    res = (sum(lst))
    return res
    
# Used to compute review score
def get_total(x, d):
    s = 0
    for q in x:
        if q.tot != None:
            s += q.tot
    if d <= 0:
        return s
    else:
        res = s / d
        return res
    
def days_between(d1, d2):
    import datetime
    a = datetime.datetime.strptime(str(d1), "%Y-%m-%d").date()
    b = datetime.datetime.strptime(str(d2), "%Y-%m-%d").date()
    res = b - a
    return int(res.days)

def current_date():
    date = datetime.now()
    converted = date.date()
    return converted

 
def can_cancel(status, arrival):
    if status != "Confirmed":
        return False
    return date.today() <= arrival - timedelta(days=2)  
    # FIXED: was `< arrival`, which allowed cancellation right up to the day before 
    # arrival, not honoring the real 48h policy

# add day
def add_days(d1, num_of_days):
    from datetime import datetime, timedelta
    #today = datetime.now()
    deadline = d1 + timedelta(days=num_of_days)
    return deadline

def number_generator():
    # create a random hex of 4 bytes
    random_hex = secrets.token_hex(4)
    a = 'BRZ00'
    booking_number = f'{a}'+ random_hex
    return booking_number

# transacion fee calculator helper function
def fee_calculator(bill, percentage=10, divider=100):
    trasaction_fee = (bill * percentage ) / divider
    return trasaction_fee

# Sanitization Use Bleach to clean HTML
ALLOWED_TAGS = []  # safest: no HTML allowed
ALLOWED_ATTRIBUTES = {}
def sanitize_input(text):
    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

