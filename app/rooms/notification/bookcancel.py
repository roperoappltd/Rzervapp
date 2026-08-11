
import logging
import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from app import mail
from app.models.roommodel import Rooms
from datetime import datetime
import random

def book_cancellation_email(booking, room_id):
    '''This function enable to send a booking confirmation message'''
    room = Rooms.query.get_or_404(room_id)
    now = datetime.now()
    date = now.strftime("%d/%m/%Y %H:%M")
    # message
    msg = Message('Booking Cancellation.', 
                  sender='dmc.partners@yahoo.com',
                  recipients=[booking.pguest_email])
    msg.html = f'''\
    <!DOCTYPE html>
    <html>
        <head>
            <style>
                .styled {{
                    border: 0;
                    line-height: 2.5;
                    padding: 0 20px;
                    font-size: 1rem;
                    text-align: center;
                    color: #fff;
                    text-shadow: 1px 1px 1px #000;
                    border-radius: 10px;
                    background-color: rgba(220, 0, 0, 1);
                    background-image: linear-gradient(
                    to top left, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.2) 30%, rgba(0, 0, 0, 0));
                    box-shadow:
                    inset 2px 2px 3px rgba(255, 255, 255, 0.6),
                    inset -2px -2px 3px rgba(0, 0, 0, 0.6);
                }}

                .styled:hover {{
                    background-color: rgba(255, 0, 0, 1);
                }}

                .styled:active {{
                    box-shadow:
                    inset -2px -2px 3px rgba(255, 255, 255, 0.6),
                    inset 2px 2px 3px rgba(0, 0, 0, 0.6);
                }}

                a.styled{{
                    cursor: pointer;
                }}

            </style>
        </head>
        <body>

            <div style="font-size: 0px; display: flex; justify-content: center">
                <img
                    class="t18"
                    style=" display: block; border: 0; height: auto; width: 20%; margin: 20px; max-width: 100%;"
                    width="188"
                    height="100"
                    alt=""
                    src="{{{url_for('static', filename='resources/img/logo/Jamlogo1g.png')}}}"
                />
            </div>
            &nbsp;<br>

            <h2>Hello { booking.primary_guest },</h2>

            <p style="font-size: 15px;">We're contacting you in regard to your
            booking cancelation request received on {date}. Please click the 
            button below to view your cancellation summary. </p>
            <div>&nbsp;</div>
            <a href="{ url_for('main.bookcancel',room_id=room.id, _external=True) }">
            <button class="favorite styled" type="button">Cancellation summary</button></a>

            <div>&nbsp;</div>
            <h4 style="font-size: 16px;"> Kind regards <br/> 
            Jambo <br/> 
            Customer service.</h4>
            <p  style="text-align:center">Copyright © 2025 Jambo.ci . All Rights Reserved. | <small class="text-warning font-italic text-capitalize">Powered by <a href="https://tboss.ci/" style="text-decoration:none;">Techno|Boss</a></small></p>

        </body>
    </html>
    '''
    # Sending the message
    mail.send(msg)
