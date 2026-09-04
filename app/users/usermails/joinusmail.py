from flask_mail import Message
from app import mail
from flask import url_for
from datetime import datetime
from flask_babel import _, force_locale

#-----------------------------------------------------------------------------------------------------
def member_regismail(user):
    '''This function enable to send a welcome message at first registration'''
    now = datetime.now()
    date = now.strftime("%d/%m/%Y %H:%M")
    token = user.get_verification_token()

    # AMENDED: previously every string below was hardcoded English, with
    # no _() wrapping at all -- the email was always English regardless
    # of the recipient's actual language. force_locale(user.language)
    # temporarily overrides the active locale for the duration of this
    # block, using the RECIPIENT's own stored preference (not whoever
    # happens to be browsing when this function is called) -- this is
    # flask_babel's documented pattern specifically for exactly this
    # "translate content for someone other than the current viewer" case.
    with force_locale(user.language):
        subject = _('Verify & activate your Jambo account')

        greeting = _('Hello %(name)s,', name=user.first_name)

        intro = _(
            'We would like to thank you for your registration received today. ' #%(date)s
            'We wish you a warm welcome to the "Jambo community". ',
            date=date
        )

        cta_text = _('Click on the button below to verify and activate your account and start your Jambo adventure.')
        button_text = _('Verify & Activate your account')
        regards = _('Kind regards')
        customer_service = _('Customer Service.')
        copyright_text = _('Copyright © %(year)s Jambo. All Rights Reserved.', year=now.year)
        powered_by = _('Powered by')

    # sending the password reset message
    msg = Message(subject, 
                  sender=('Jambo Booking', 'ropero.app@gmail.com'),
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

        <div style="font-size: 0px; display: flex; justify-content: center">
            <img
                class="t18"
                style=" display: block; border: 0; height: auto; width: 20%; margin: 20px; max-width: 100%;"
                width="188"
                height="100"
                alt=""
                src="{url_for('static', filename='userpics/pics/logojam.png', _external=True)}"
            />
        </div>
        &nbsp;<br>

        <h2>{greeting}</h2>

        <p style="font-size: 18px; text-align:justify;"> {intro}
        <br>
        &nbsp;<br>
        {cta_text}
        </p>

        <div>&nbsp; &nbsp;</div>
        
        <a href="{ url_for('users.verify_email', token=token, _external=True)}">
        <button class="favorite styled" type="button">{button_text}</button></a>

        <div>&nbsp;</div>
        <h3> {regards} <br/> <b>Jambo</b> <br/> {customer_service}</h3>
        <p  style="text-align:center">{copyright_text} | <small class="text-warning font-italic text-capitalize">{powered_by} <a href="https://tboss.ci/" style="text-decoration:none;">Techno Boss Intl.</a></small></p>

    </body>
</html>
'''
    # Sending the message
    mail.send(msg)