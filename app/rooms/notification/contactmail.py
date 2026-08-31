import logging
import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from app import mail
# from app.models.roommodel import Rooms
# from app.models.bookmodel import Bookings
from datetime import datetime
from ..roomutils import sanitize_input
# import random
from dotenv import load_dotenv

load_dotenv()


def karibu_contact(form):
    '''This function enable to send a contact message'''
    clean_msg = sanitize_input(form.message.data)
    now = datetime.now()
    date = now.strftime("%d/%m/%Y %H:%M")
    # message
    msg = Message(f"Contact Form: { form.subject.data } ", 
                  sender= ('Jambo Booking', 'ropero.app@gmail.com'), 
                  recipients=['jambo@tbossci.com'],
                  reply_to=form.email.data)
    
    msg.html = f'''\
    <!DOCTYPE html>
    <html>
        <body>
            <div style="font-size: 0px; display: flex; justify-content: center">
                <img
                    class="t18"
                    style=" display: block; border: 0; height: auto; width: 20%; margin: 20px; max-width: 100%;"
                    width="188"
                    height="100"
                    alt=""
                    src="{ url_for('static', filename='resources/img/logo/Jamlogo1g.png') }"
                />
            </div>
            &nbsp;<br>

            <h5>Subject: {form.subject.data},</h5>
            <hr>
            <p style="font-size: 13px;">Date: { date }</p>
            <hr>
            <p style="font-size: 13px;">{ clean_msg }</p>
            <hr>
            <div>&nbsp;</div>
            <h4 style="font-size: 13px;">
                Kind regards <br/> 
                Name: { form.name.data } <br/> 
                Email: { form.email.data }
            </h4>

            <p  style="text-align:center">
                Copyright © 2026 Jambo Contact Form . 
                All Rights Reserved. | <small class="text-warning font-italic text-capitalize">
                Powered by <a href="https://tboss.ci/" style="text-decoration:none;">Techno|Boss</a>
                </small>
            </p>
        </body>
    </html>
    '''
    # Sending the message
    mail.send(msg)
