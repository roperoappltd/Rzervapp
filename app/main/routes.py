from flask import (Blueprint, render_template, flash, redirect, url_for, session, 
                   current_app, request) 
from flask_login import current_user, login_required
from app import db
from app.models.roommodel import Rooms, Deals
from app.models.bookmodel import Bookings
from app.models.usermodel import ContactMsg
from ..rooms.roomutils import sanitize_input
from .forms import ContactForm
# from ..rooms.roomutils import current_date
from flask_mail import Message
from app import mail
from app.rooms.notification.contactmail import karibu_contact
from sqlalchemy.sql.expression import func
import os
from dotenv import load_dotenv
from flask_babel import gettext, _

load_dotenv()

# Creating an instance of the blueprint class
main = Blueprint('main', __name__)

@main.route("/")                                                     
@main.route("/home") 
def home():
    '''This function create a route to render the home page'''
    # Randomly query the fourth latest available rooms
    latest_rooms =  (Rooms.query.filter_by(status='Available')
                                 .order_by(db.func.random())
                                 .limit(3).all())
    # Every 4 rooms  
    featured_rooms = (Rooms.query.order_by(
                      Rooms.created_at.desc())
                     .offset(4).limit(4).all())
    # Latest room available
    spotlight =  (Rooms.query.order_by(
                  Rooms.updated_at.desc()).first())
    # weekend deals
    weekend_room = (Rooms.query.order_by(db.func.random()).first())
    wkend_deal = db.session.query(Deals).filter(Deals.name == 'Weekend Deal').first()
    offer_1 = float(weekend_room.price) - ( float(weekend_room.price) * (wkend_deal.discount_percent / 100)) 
    # weekday deals
    weekday_room = (Rooms.query.order_by(db.func.random()).first())
    wkday_deal = db.session.query(Deals).filter(Deals.name == 'Weekday Deal').first()
    offer_2 = float(weekday_room.price) - ( float(weekday_room.price) * (wkday_deal.discount_percent / 100)) 
    # Romantic deal
    romantic_room = (Rooms.query.order_by(db.func.random()).first())
    rom_deal = db.session.query(Deals).filter(Deals.name == 'Romantic Getaway').first()
    offer_3 = float(romantic_room.price) - ( float(romantic_room.price) * (rom_deal.discount_percent / 100))  

    # Query first image
    image1 = url_for('static', filename='userpics/roompics/' + spotlight.image1)

    return render_template('pages/homes.html',  title='Home', spotlight=spotlight, 
                            image1=image1, latest_rooms=latest_rooms, featured_rooms=featured_rooms,
                            weekend_room=weekend_room, weekday_room=weekday_room,
                            romantic_room=romantic_room, wkend_deal=wkend_deal,
                            wkday_deal=wkday_deal, rom_deal=rom_deal, offer_1=offer_1,
                            offer_2=offer_2, offer_3=offer_3)

@main.route("/about") 
def about():
    '''This function create a route to render the about page'''
    
    return render_template('pages/aboutus.html', title='About us')

@main.route("/behost") 
def behost():
    '''This function create a route to render the Be host page'''
    
    return render_template('pages/behost.html', title='Become Host')

# Language Switcher api
@main.route("/set-language/<lang>")
def set_language(lang):
    if lang in ["en", "fr"]:
        session["language"] = lang
    
    return redirect(request.referrer or url_for("main.home"))

# Currency selector 
@main.route("/set-currency/<currency>")
def set_currency(currency):

    allowed = ["GBP","EUR","USD","XOF","XAF","NGN","GHS","KES",
               "UGX","RWF","TZS","MAD","EGP","ZAR","JPY"]

    if currency not in allowed:
        return redirect(request.referrer or url_for("main.home"))

    session["currency"] = currency

    if current_user.is_authenticated:
        current_user.preferred_currency = currency
        db.session.commit()

    return redirect(request.referrer or url_for("main.home"))

#================================================

@main.route("/bookconfirm/<int:booking_id>", methods=['GET', 'POST']) 
def bookconfirm(booking_id):
    '''This function create a route to render booking summary page'''
    booking = (Bookings.query
                .filter_by(id=booking_id)
                .first_or_404()
                )
    
    return render_template('pages/bookingmsg.html', title='Booking Summary',
                            booking=booking)

@main.route("/bookcancel:/<int:booking_id>", methods=['GET', 'POST']) 
#@login_required
def bookcancel(booking_id):
    '''This function create a route to render cancellation summary page'''
    booking = (
                Bookings.query
                .filter_by(id=booking_id)
                .first_or_404()
            )
    
    return render_template('pages/bookcancelmsg.html', title='Cancellation',
                            booking=booking)

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    # creating contact form object 
    form = ContactForm()
    try:
        if form.validate_on_submit():    
            # Sanitize user msg
            clean_msg = sanitize_input(form.message.data)
            # Recording message on db
            contact = ContactMsg(name=form.name.data, email=form.email.data,
                                subject=form.subject.data, message=clean_msg)
            db.session.add(contact)
            db.session.commit()
            # flash("Your message has been recorded in our DB.", "success")
            #-----------------------------------------------------------------------
            # send the email
            # karibu_contact(form)
            msg = Message( f"Contact Form: {form.subject.data}",
                           sender=os.getenv("EMAIL_USER"), #'dmc.partners@yahoo.com',
                           recipients=['dmc.partners1@gmail.com'])
            msg.body = f"""
Sender Name: { form.name.data}
Sender Email: { form.email.data }
------------------------------------------------------------------------------------
Sender Message: { clean_msg }
"""
            # sending email
            mail.send(msg)
            # email sending confirmation
            flash(_("Your message has been sent successfully."), "success")

            return redirect(url_for('main.contact'))

    except Exception as e:
        current_app.logger.error(f"Mail send failed: {e}")
            
    return render_template('/pages/getintouch.html', title='Contact us', form=form)