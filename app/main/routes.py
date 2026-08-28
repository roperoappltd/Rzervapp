from flask import (Blueprint, render_template, flash, redirect, url_for, session, 
                   current_app, request) 
from decimal import Decimal
from flask_login import current_user
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
from app.services.image_storage import get_room_image_url
from app.services.currency import convert_and_format, get_exchange_rates
from app.services.preference_service import VisitorPreferences
# from sqlalchemy.sql.expression import func
import os
from dotenv import load_dotenv
from flask_babel import gettext, _

load_dotenv()

# Creating an instance of the blueprint class
main = Blueprint('main', __name__)

# @main.route("/")                                                     
# @main.route("/home") 
# def home():
#     '''This function create a route to render the home page'''
#     # Randomly query the fourth latest available rooms
#     latest_rooms =  (Rooms.query.filter_by(status='Available')
#                                  .order_by(db.func.random())
#                                  .limit(3).all())
#     # Every 4 rooms  
#     featured_rooms = (Rooms.query.order_by(
#                       Rooms.created_at.desc())
#                      .offset(4).limit(4).all())
#     # Latest room available
#     spotlight =  (Rooms.query.order_by(
#                   Rooms.updated_at.desc()).first())
#     # weekend deals
#     weekend_room = (Rooms.query.order_by(db.func.random()).first())
#     wkend_deal = db.session.query(Deals).filter(Deals.name == 'Weekend Deal').first()
#     offer_1 = float(weekend_room.price) - ( float(weekend_room.price) * (wkend_deal.discount_percent / 100)) #if wkend_deal and wkend_deal else 0
#     # weekday deals
#     weekday_room = (Rooms.query.order_by(db.func.random()).first())
#     wkday_deal = db.session.query(Deals).filter(Deals.name == 'Weekday Deal').first()
#     offer_2 = float(weekday_room.price) - ( float(weekday_room.price) * (wkday_deal.discount_percent / 100)) #if wkend_deal and wkend_deal else 0
#     # Romantic deal
#     romantic_room = (Rooms.query.order_by(db.func.random()).first())
#     rom_deal = db.session.query(Deals).filter(Deals.name == 'Romantic Getaway').first()
#     offer_3 = float(romantic_room.price) - ( float(romantic_room.price) * (rom_deal.discount_percent / 100))  #if romantic_room and rom_deal else 0

#     # Query first image
#     image1 = url_for('static', filename='userpics/roompics/' + spotlight.image1)

#     return render_template('pages/homes.html',  title='Home', spotlight=spotlight, 
#                             image1=image1, latest_rooms=latest_rooms, featured_rooms=featured_rooms,
#                             weekend_room=weekend_room, weekday_room=weekday_room,
#                             romantic_room=romantic_room, wkend_deal=wkend_deal,
#                             wkday_deal=wkday_deal, rom_deal=rom_deal, offer_1=offer_1,
#                             offer_2=offer_2, offer_3=offer_3)

 
import random as pyrandom

def get_random_rooms(n=1, status=None):
    '''Returns up to n randomly-selected rooms. Deliberately avoids
    func.random() -- SQLAlchemy emits that as the literal SQL random(),
    which SQLite understands natively but MySQL does not (MySQL's
    equivalent is RAND(), a different function name). Doing the
    randomization in Python instead keeps this portable across both
    without needing to branch on which dialect is active.'''
    query = Rooms.query
    if status:
        query = query.filter_by(status=status)
    room_ids = [r.id for r in query.with_entities(Rooms.id).all()]
    if not room_ids:
        return []
    chosen_ids = pyrandom.sample(room_ids, min(n, len(room_ids)))
    return Rooms.query.filter(Rooms.id.in_(chosen_ids)).all()


@main.route("/")                                                     
@main.route("/home") 
def home():
    '''This function create a route to render the home page'''
    # Randomly query the fourth latest available rooms
    latest_rooms = get_random_rooms(n=3, status='Available')
    # Every 4 rooms  
    featured_rooms = (Rooms.query.order_by(
                      Rooms.created_at.desc())
                     .offset(4).limit(4).all())
    # Latest room available
    spotlight =  (Rooms.query.order_by(
                  Rooms.updated_at.desc()).first())
 
    # AMENDED: on a fresh/empty database (no rooms seeded yet), every
    # .first() below can return None -- previously this crashed
    # immediately with AttributeError the moment anyone visited "/".
    # Guarding each one so the homepage degrades gracefully instead.
 
    # --------------------------------------------------
    # Host-set discounted rooms -- up to 3 shown at random. Hosts don't
    # choose a category when setting a discount (just a percentage), so
    # each selected room gets a randomly-assigned display label purely
    # for visual variety on the card -- these are NOT tied to any real
    # weekend/weekday/romantic logic, just decorative copy. Replaces the
    # old system of 3 fixed named campaigns each paired with a random
    # room, since that's unrelated to actual host-set discounts.
    # --------------------------------------------------
    deal_card_styles = [
        {"title": _("Weekend Getaway Deal"), "subtext": _("Perfect for a quick escape")},
        {"title": _("Weekday Massive Deal"), "subtext": _("Great value any day of the week")},
        {"title": _("Couples Great Savings"), "subtext": _("Available year-round")},
    ]

    active_deals = Deals.query.filter(Deals.room_id.isnot(None), Deals.active == True).all()
    chosen_deals = pyrandom.sample(active_deals, min(3, len(active_deals)))
    chosen_styles = pyrandom.sample(deal_card_styles, len(chosen_deals))  # no repeated label among the cards shown

    # Same GBP-bridge pattern used everywhere else -- room.price is in
    # the ROOM's own currency (e.g. XOF), not GBP, so it needs converting
    # through GBP before being shown in the viewer's currency. Previously
    # these cards had a hardcoded £, which would have been actively
    # wrong the moment a non-GBP-priced room appeared here.
    guest_currency = VisitorPreferences().currency
    rates = get_exchange_rates()

    deal_cards = []
    for deal, style in zip(chosen_deals, chosen_styles):
        room = deal.room
        if not room:
            continue  # defensive -- shouldn't happen given the FK, but don't let one bad row break the whole section

        raw_room_rate = rates.get(room.room_currency)
        if raw_room_rate is None:
            continue  # no exchange rate available for this room's currency -- skip rather than show a wrong/crashing price

        # Same Decimal/float mixing fix as convert_currency() --
        # ExchangeRate.rate is a Numeric column (Decimal by default),
        # and dividing a plain float by it throws TypeError. Cast back
        # to float once the division is done, since the discount
        # percentage math right below (deal.discount_percent / 100, a
        # plain float) would hit the identical error again if
        # price_gbp were left as a Decimal.
        room_rate = Decimal(str(raw_room_rate))
        price_gbp = float(Decimal(str(room.price)) / room_rate)
        offer_price_gbp = price_gbp - (price_gbp * (deal.discount_percent / 100))

        deal_cards.append({
            "room": room,
            "deal": deal,
            "original_price_display": convert_and_format(price_gbp, "GBP", guest_currency),
            "offer_price_display": convert_and_format(offer_price_gbp, "GBP", guest_currency),
            "title": style["title"],
            "subtext": style["subtext"],
        })
 
    # Query first image -- guarded against no rooms existing at all,
    # and against a room existing but never having had an image uploaded.
    image1 = None
    if spotlight and spotlight.image1:
        image1 = get_room_image_url(spotlight.image1)
 
    # --------------------------------------------------
    # Testimonials -- shown as an auto-advancing carousel, reordered
    # randomly on every page load so the same testimonial isn't always
    # the first one visitors see. Randomized server-side (same
    # pyrandom.sample pattern as deal_cards above) rather than client-
    # side JS, so it still works correctly even if JS fails to load.
    # --------------------------------------------------
    testimonials = [
        {
            "quote": _("I booked a room in Abidjan while I was still in London, and seeing the price instantly in my own currency made the whole process feel effortless. No guesswork, no surprises at checkout — just a clear, honest price from start to finish. Jambo made booking across borders feel as simple as booking a hotel at home."),
            "image": "Damara.jpeg",
            "name": "Amara Dialo",
            "role": _("Frequent Traveler"),
        },
        {
            "quote": _("Listing my first room on Jambo took less than ten minutes, and within a week I had my first booking. Being able to set my own discount and track my earnings right from my dashboard gives me real control over my own listing. It's turned a spare room into a genuine, reliable source of income."),
            "image": "JB-Kouassi.jpeg",
            "name": "Jean-Baptiste Kouassi",
            "role": _("Host, Cocody"),
        },
        {
            "quote": _("My family is originally from Dakar, and I go back every year to visit. Being able to browse listings and book everything in French, with prices shown in euros before I even convert anything in my head, makes the whole process so much less stressful. Jambo genuinely feels like it was built with people like me in mind."),
            "image": "fatou.jpeg",
            "name": "Fatou Ndiaye",
            "role": _("Guest, Paris"),
        },
        {
            "quote": _("I was nervous about hosting for the first time, but the review system gave me confidence — guests could see I was trustworthy before they even messaged me, and I could see the same about them. Payments land in my account already converted, no confusion about exchange rates. Its been a genuinely reliable way to earn extra income from a room I was not using."),
            "image": "kamau.jpeg",
            "name": "Wanjiru Kamau",
            "role": _("Host, Nairobi"),
        },
    ]
    testimonials = pyrandom.sample(testimonials, len(testimonials))

    return render_template('pages/homes.html',  title='Home', spotlight=spotlight, 
                            image1=image1, latest_rooms=latest_rooms, featured_rooms=featured_rooms,
                            deal_cards=deal_cards, testimonials=testimonials)

@main.route("/about") 
def about():
    '''This function create a route to render the about page'''
    
    return render_template('pages/aboutus.html', title='About us')

@main.route("/terms-of-use")
def terms_of_use():
    '''This function create a route to render the terms of use page'''

    return render_template('pages/terms_of_use.html', title='Terms of Use')

@main.route("/payment-policy")
def payment_policy():
    '''This function create a route to render the paymenty policy page'''

    return render_template('pages/payment_policy.html', title='Terms of Use')

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
            
    return render_template('pages/getintouch.html', title='Contact us', form=form)