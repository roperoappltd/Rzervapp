from flask_mail import Message
from app import mail
from flask import url_for
from datetime import datetime

#-----------------------------------------------------------------------------------------------------
def member_regismail(user):
    '''This function enable to send a welcome message at first registration'''
    now = datetime.now()
    date = now.strftime("%d/%m/%Y %H:%M")
    # sending the password reset message
    msg = Message('Thanks for joining us', 
                  sender='dmc.partners@yahoo.com',
                  recipients=[user.email])
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
                background-color: rgba(0, 150, 255, 1);
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

        <h2>Hello {user.username},</h2>

        <p style="font-size: 18px; text-align:justify;"> We would like to thank you for your registration
        received today {date}. We wish you a warn Welcome to the "Rezerva plateform" where you can reserve
        short stay safer, happier and cheaper. Click on the button below to activate your acount and start
        experiencing the wonders of this world.
        </p>

        <div>&nbsp; &nbsp;</div>
        
        <a href="{ url_for('main.home', _external=True)}">
        <button class="favorite styled" type="button">Activate your account</button></a>

        <div>&nbsp;</div>
        <h3> Kind regards <br/> <b>Rezerva</b> <br/> Customer Service.</h3>
        <p  style="text-align:center">Copyright © 2026 Rezerva. All Rights Reserved. | <small class="text-warning font-italic text-capitalize">Powered by <a href="https://tboss.ci/" style="text-decoration:none;">Techno Boss Intl.</a></small></p>

    </body>
</html>
'''
    # Sending the message
    mail.send(msg)