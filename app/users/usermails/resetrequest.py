from flask_mail import Message
from app import mail
from flask import url_for

#-----------------------------------------------------------------------------------------------------
def send_reset_email(user):
    '''This function enable to send a password reset request email link'''
    # generate a token
    token = user.get_reset_token()
    # sending the password reset message
    msg = Message('Password reset request', 
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

        <h2>Hello {user.username},</h2>

        <p style="font-size: 18px; text-align:justify;">A request has been made for a password reset. 
        Please, click on the button below to reset your password. if the request was not made by you, 
        please contact us so that we can investigate further. Please, be informed that the link is 
        only valid for 10 minutes.</p>

        <div>&nbsp; &nbsp;</div>
        
        <a href="{ url_for('users.reset_token', token=token, _external=True)}">
        <button class="favorite styled" type="button">Reset your password</button></a>

        <div>&nbsp;</div>
        <h3> Kind regards <br/> <b>Rezerva</b> <br/> IT Team.</h3>
        <p  style="text-align:center">Copyright © 2026 Rezerva. All Rights Reserved. | <small class="text-warning font-italic text-capitalize">Powered by <a href="https://tboss.ci/" style="text-decoration:none;">Techno Boss Intl.</a></small></p>

    </body>
</html>
'''
    # Sending the message
    mail.send(msg)