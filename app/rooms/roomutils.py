import logging
import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_login import current_user
from flask_mail import Message
from app import mail
from app.services.image_storage import upload_room_image
from app import db
from app.models.roommodel import Roomreviews

def get_ratings_for_rooms(room_ids):
    '''One query for every room's rating in a list, instead of a
    separate query per card. Shared by room() and roomsearch() so the
    same logic isn't duplicated across route files.
    Returns {room_id: {'score': float, 'count': int}, ...} -- a room
    with zero (or only unpublished) reviews simply won't be a key here.'''
    if not room_ids:
        return {}
    rating_rows = (
        db.session.query(
            Roomreviews.room_id,
            db.func.avg(Roomreviews.rate_us).label('avg_rating'),
            db.func.count(Roomreviews.id).label('review_count'),
        )
        .filter(Roomreviews.room_id.in_(room_ids), Roomreviews.status == 'Published')
        .group_by(Roomreviews.room_id)
        .all()
    )
    return {
        row.room_id: {'score': round(float(row.avg_rating), 1), 'count': row.review_count}
        for row in rating_rows
    }

import cv2
import bleach
from datetime import *



# Create a function that handle profile picture
def save_picture(form_picture):
    '''This function resizes an uploaded picture and stores it via the
    image storage abstraction (local disk or Cloudinary, per
    Config.IMAGE_BACKEND) -- returns a KEY to save on the Rooms row,
    never a full URL. See app/services/image_storage.py.'''
    # create a random hex of 4 bytes
    random_hex = secrets.token_hex(4)
    # combine with the username to build a unique key for this upload
    key_hint = f'{current_user.username}' + random_hex
    # Resizing the picture before saving
    img_sizer = (960, 640)
    new_img = Image.open(form_picture)
    new_img.thumbnail(img_sizer)
    # Store via the active backend (local disk in dev, Cloudinary in
    # production) -- returns the key, not a full URL.
    return upload_room_image(new_img, key_hint)

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