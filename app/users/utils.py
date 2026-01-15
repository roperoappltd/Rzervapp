import logging
import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from app import mail


# Create a function that handle profile picture
def save_picture(form_picture):
    '''This function add random hex byte & extension to a file a save to a location '''
    # create a random hex of 8 bytes
    random_hex = secrets.token_hex(8)
    # slice the file name and file extension of the picture update
    _, file_ext = os.path.splitext(form_picture.filename)
    # combine the random hex with the file extension in order set the name of the new uploaded file
    uploaded_PicName = random_hex + file_ext 
    # extract and define the path where to save the file
    picture_path = os.path.join(current_app.root_path, 'static/profile/', uploaded_PicName)
    # Resizing the  picture before saving
    img_sizer = (125, 125)
    new_img = Image.open(form_picture)
    new_img.thumbnail(img_sizer)
    # Saving the picture
    new_img.save(picture_path)
    return uploaded_PicName