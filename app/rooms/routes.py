from flask import (Blueprint, render_template, flash, abort, redirect, request, jsonify,
                   session, url_for, current_app)
from flask_login import current_user, login_required
from app import db
from wtforms.validators import ValidationError
# from app.models.usermodel import User
from app.models.roommodel import (Rooms, Roomextra, Roomreviews, Deals, RoomBlock, 
                                  ReviewHelpful, RoomView)
from app.models.bookmodel import Bookings, Vouchers, Payments, HostEarning, VoucherUsage
# from app.models.chatmodel import Conversation
from app.rooms.forms import (UpdateRoomForm, UpdateRoomPictureForm, PaymentForm, RoomSearchForm,
                            RoomExtraForm, RoomReviewsForm, BookingForm)
from .roomutils import (save_picture, sanitize_input, fee_calculator, 
                        can_cancel, get_ratings_for_rooms)
# from ..users.utils import get_location
from .notification.bookmail import booking_confirm_email
from .notification.bookcancel import book_cancellation_email
# from sqlalchemy import func
from datetime import datetime, date
# from sqlalchemy import or_
from app.helpers.populate_search import populate_search_choices
# from app.helpers.is_avail import is_available
from app.helpers.booking import create_booking, get_room_active_deal
from app.helpers.searches import build_room_query
from app.helpers.email_verify import email_verified_required
from app.helpers.cancel_checks import cancel_and_refund_if_paid
from decimal import Decimal
from app.services.currency import get_exchange_rates, get_symbol 
from app.services.preference_service import VisitorPreferences
from flask_babel import _

# Creating an instance of the blueprint class
bedrooms = Blueprint('bedrooms', __name__)

# @bedrooms.route("/room") 
# def room():
#     '''This function create a route to render the rooms page'''
#     #room = Rooms.query.get_or_404(room_id)
#     #dt = booker.created_at
#     #deadlines = deadline(dt.date(), 2)
#     form = RoomSearchForm()
#     populate_search_choices(form)
#     # Set a specific page to start with 
#     page = request.args.get('page', 1, type=int)
#     # Query db to display specific number of room per page (Pagination)
#     allrooms = Rooms.query.filter(Rooms.status == "Available"
#                                  ).order_by(Rooms.updated_at.desc()
#                                            ).paginate(page=page, per_page=6,
#                                                       error_out=False
#                                                       )

#     # Search rooms with expired booking 
#     expired_bookings = Bookings.query.filter(
#                        Bookings.departure < datetime.now()
#                        ).all()

#     # Iterate over the list of bookings
#     for booking in expired_bookings:
#         booking.active = False
#         booking.status = 'Expired'
#         #conversation.active = False
#     # Save the changes in db
#     db.session.commit()

#     # Search for canccelled booking
#     cancelled_bookings = Bookings.query.filter(
#                          Bookings.status == 'Cancelled',
#                          Bookings.active == True
#                         ).all()

#     for booking in cancelled_bookings:
#         booking.active = False
#         #conversation.active = False

#     db.session.commit()

#     return render_template('pages/rooms.html', title='Rooms Pool', allrooms=allrooms, form=form)

@bedrooms.route("/room") 
def room():
    '''This function create a route to render the rooms page'''
    #room = Rooms.query.get_or_404(room_id)
    #dt = booker.created_at
    #deadlines = deadline(dt.date(), 2)
    form = RoomSearchForm()
    populate_search_choices(form)
    # Set a specific page to start with 
    page = request.args.get('page', 1, type=int)
    # Query db to display specific number of room per page (Pagination)
    allrooms = Rooms.query.filter(Rooms.status == "Available"
                                 ).order_by(Rooms.updated_at.desc()
                                           ).paginate(page=page, per_page=6,
                                                      error_out=False
                                                      )
 
    # One query for every room's rating on this page, instead of a
    # separate query per card -- see get_ratings_for_rooms() in
    # rooms/roomutils.py (shared with roomsearch() below).
    room_ids = [r.id for r in allrooms.items]
    ratings_by_room = get_ratings_for_rooms(room_ids)
 
    # Search rooms with expired booking 
    expired_bookings = Bookings.query.filter(
                       Bookings.departure < datetime.now()
                       ).all()
 
    # Iterate over the list of bookings
    for booking in expired_bookings:
        booking.active = False
        booking.status = 'Expired'
        #conversation.active = False
    # Save the changes in db
    db.session.commit()
 
    # Search for canccelled booking
    cancelled_bookings = Bookings.query.filter(
                         Bookings.status == 'Cancelled',
                         Bookings.active == True
                        ).all()
 
    for booking in cancelled_bookings:
        booking.active = False
        #conversation.active = False
 
    db.session.commit()
 
    return render_template('pages/rooms.html', title='Rooms Pool', allrooms=allrooms,
                          form=form, ratings_by_room=ratings_by_room)

@bedrooms.route("/roomsearch", methods=["GET", "POST"])
def roomsearch():
    # Set a specific page to start with
    page = request.args.get('page', 1, type=int)
 
    form = RoomSearchForm()
    populate_search_choices(form)
 
    # Navbar search parameters
    location = request.args.get("location", "").strip()
    borough = None
    arrival = request.args.get("arrival", "")
    departure = request.args.get("departure", "")
 
    room_category = None
    min_price = None
    max_price = None
 
    # --------------------------------------------------
    # ADVANCED WTF FILTERS
    # --------------------------------------------------
    if form.validate_on_submit():
        if form.room_location.data:
            location = form.room_location.data
        if form.borough.data:
            borough = form.borough.data
        room_category = form.room_category.data
        min_price = form.min_price.data
        max_price = form.max_price.data
 
    result = build_room_query(
        location=location, borough=borough, room_category=room_category,
        min_price=min_price, max_price=max_price,
        arrival=arrival, departure=departure,
    )
 
    if result["error"] == "invalid_dates":
        flash(_("Invalid arrival or departure date."), "warning")
        return render_template("pages/roomsearched.html", title="Search Results",
                              form=form, rooms_found=None, ratings_by_room={})
 
    if result["error"] == "departure_before_arrival":
        flash(_("Departure date must be after arrival date."), "warning")
        return render_template("pages/roomsearched.html", title="Search Results",
                              form=form, rooms_found=None, ratings_by_room={})
 
    if result["error"] == "no_availability":
        rooms_found = result["query"].paginate(page=page, per_page=6, error_out=False)
        flash(_("No rooms available for the selected dates."), "warning")
        return render_template("pages/roomsearched.html", title="Search Results",
                              form=form, rooms_found=rooms_found, arrival=arrival,
                              departure=departure, location=location, ratings_by_room={})
 
    # --------------------------------------------------
    # PAGINATION
    # --------------------------------------------------
    rooms_found = result["query"].order_by(Rooms.created_at.desc()).paginate(
                                 page=page, per_page=6, error_out=False)
    if rooms_found.total == 0:
        flash(_("No rooms found. Please refine your search."), "warning")
 
    # Same shared helper as room() -- one query for all rooms on this
    # results page instead of one per card.
    ratings_by_room = get_ratings_for_rooms([r.id for r in rooms_found.items])
 
    return render_template("pages/roomsearched.html", title="Search Results",
                            form=form, rooms_found=rooms_found, arrival=arrival,
                            departure=departure, location=location, ratings_by_room=ratings_by_room)
 

@bedrooms.route("/booknow/<int:room_id>", methods=['GET', 'POST'])
@login_required 
@email_verified_required
def booknow(room_id):
    '''This function create a route to render the booking page'''
    # fetch the room by id if exist or return 404 if doesnt
    room = Rooms.query.get_or_404(room_id)
    # create room reviews form
    form = BookingForm()

    # Get the deal id    
    deal_id = request.args.get('deal_id', type=int)
    # default value
    deal = None
    if deal_id:
        deal = Deals.query.get_or_404(deal_id)

    if form.validate_on_submit():
        bookinfo, error = create_booking(
            room=room, arrival=form.arrival.data, departure=form.departure.data, 
            primary_guest=form.primary_guest.data, pguest_email=form.pguest_email.data,
            pguest_phone=form.pguest_phone.data, ad_info=form.ad_info.data,
            user_id=current_user.id, deal_id=deal_id
        )

        if error:
            flash(error, "danger")
            return redirect(url_for('bedrooms.room'))

        flash(_('Booking submitted successfully. Proceed to checkout!'), 'success')
        return redirect(url_for('bedrooms.checkout', room_id=room.id))
    
    elif request.method == 'GET':
        form.room_type.data = room.room_category
        form.num_guests.data = room.max_occupancy
                
    return render_template('pages/booking.html', title='Booking', form=form, room=room)


# @bedrooms.route("/api/agent/booknow", methods=['POST'])
# @login_required
# @email_verified_required
# def agent_booknow():
#     '''
#     JSON booking endpoint for the AI booking agent.

#     Expected JSON body:
#     {
#       "room_id": 12,
#       "arrival": "2026-08-10",     # ISO date string, parsed below
#       "departure": "2026-08-14",
#       "primary_guest": "Jane Doe",
#       "pguest_email": "jane@exampl  e.com",
#       "pguest_phone": "+225...",
#       "ad_info": "Late check-in around 9pm",   # optional
#       "deal_id": null                           # optional
#     }


#     IMPORTANT: the agent must only call this after the user has
#     explicitly confirmed the booking details in the conversation --
#     this route performs a real, state-changing action (creates a
#     booking and blocks the room), unlike the read-only search route.
#     '''
#     data = request.get_json(silent=True) or {}

#     room_id = data.get('room_id')
#     if not room_id:
#         return jsonify(success=False, error="Missing room_id."), 400

#     room = Rooms.query.get_or_404(room_id)

#     try:
#         arrival = datetime.strptime(data.get('arrival', ''), '%Y-%m-%d').date()
#         departure = datetime.strptime(data.get('departure', ''), '%Y-%m-%d').date()
#     except (ValueError, TypeError):
#         return jsonify(success=False, error="Invalid or missing arrival/departure date (expected YYYY-MM-DD)."), 400

#     primary_guest = (data.get('primary_guest') or '').strip()
#     pguest_email = (data.get('pguest_email') or '').strip()
#     pguest_phone = (data.get('pguest_phone') or '').strip()

#     if not primary_guest or not pguest_email or not pguest_phone:
#         return jsonify(success=False, error="Missing guest name, email, or phone."), 400

#     bookinfo, error = create_booking(room=room, arrival=arrival,
#                                     departure=departure, primary_guest=primary_guest,
#                                     pguest_email=pguest_email, 
#                                     pguest_phone=pguest_phone,
#                                     ad_info=data.get('ad_info', ''),
#                                     user_id=current_user.id,
#                                     deal_id=data.get('deal_id'),
#                                 )

#     if error:
#         return jsonify(success=False, error=error), 409

#     return jsonify(
#         success=True,
#         booking_num=bookinfo.booking_num,
#         room_id=room.id,
#         num_guests=bookinfo.num_guests,
#         checkout_url=url_for('bedrooms.checkout', room_id=room.id),
#     )

 
@bedrooms.route("/cancel-booking/<int:booking_id>", methods=['POST'])  # FIXED: removed GET -- state-changing action, GET bypasses CSRF protection entirely
@login_required 
def cancel_booking(booking_id):
    booking = Bookings.query.get_or_404(booking_id)
 
    # Security check
    if booking.user_id != current_user.id:
        abort(403)
 
    # Prevent double cancellation
    if booking.status == "Cancelled":
        flash(_("Booking already cancelled."), "warning")
        return redirect(url_for('bedrooms.bookings'))
 
    # Single source of truth for whether self-service cancellation is
    # currently allowed (must be Confirmed AND within the 48h window).
    if not can_cancel(booking.status, booking.arrival):
        flash(_("This booking can no longer be cancelled online. Please contact us for assistance."), "warning")
        return redirect(url_for('bedrooms.bookings'))
 
    payment = Payments.query.filter_by(booking_id=booking.id).first()
    if payment is None:
        # Shouldn't happen if "Confirmed" always implies a completed
        # payment -- guarding against it rather than crashing.
        flash(_("No payment record found for this booking. Please contact us."), "danger")
        return redirect(url_for('bedrooms.bookings'))
 
    # Cancel booking + create refund (shared logic, also used by
    # delete_account() when a user's own upcoming trip gets auto-cancelled)
    cancel_and_refund_if_paid(booking)
    db.session.commit()
 
    room_id = booking.room_id
    book_cancellation_email(booking, room_id)
    flash(_('Link to view cancellation summary sent to %(email)s.', email=booking.pguest_email), 'success')  # FIXED: f-string inside _() silently broke translation
 
    return redirect(url_for('bedrooms.bookings'))
    
 
TWO_DP = Decimal('0.01')
 

@bedrooms.route("/checkout/<int:room_id>", methods=['GET', 'POST']) 
@login_required
def checkout(room_id):
    '''This function create a route to handle checkout''' 
    room = Rooms.query.get_or_404(room_id)
    book = db.session.query(Bookings).with_for_update().filter(
        Bookings.room_id == room.id,
        Bookings.status == "Pending",
        ).first()
 
    if not book:
        flash(_('Server error or booking already created.'), 'warning')
        return redirect(url_for('bedrooms.room'))
    
    #compute bookdays
    bookdays = (book.departure - book.arrival).days 
 
    if bookdays <= 0:
        flash(_("Invalid booking dates."), "warning")
        return redirect(url_for('bedrooms.roomdetail', room_id=room.id))  # FIXED: was 'rooms.roomdetail' -- wrong blueprint name, would throw BuildError
 
    # --------------------------------------------------------------
    # Currency chain: room.price (host currency) -> GBP -> guest's
    # currency. Same GBP-bridge pattern as create_booking().
    # --------------------------------------------------------------
    guest_currency = VisitorPreferences().currency
    host_currency = room.room_currency
 
    rates = get_exchange_rates()  # {currency_code: rate_per_1_gbp, ..., 'GBP': 1}
 
    raw_host_rate = rates.get(host_currency)
    if raw_host_rate is None:
        flash(_("Checkout currently unavailable: missing exchange rate for %(currency)s.", currency=host_currency), "danger")
        return redirect(url_for('bedrooms.roomdetail', room_id=room.id))
 
    raw_guest_rate = rates.get(guest_currency)
    if raw_guest_rate is None:
        flash(_("Checkout currently unavailable: missing exchange rate for %(currency)s.", currency=guest_currency), "danger")
        return redirect(url_for('bedrooms.roomdetail', room_id=room.id))
 
    rate_host = Decimal(str(raw_host_rate))
    rate_guest = Decimal(str(raw_guest_rate))
 
    # room.price is per-night, host currency.
    room_price_host = Decimal(room.price)
    room_price_gbp = room_price_host / rate_host
    # AMENDED: payment.html (pre-payment checkout page) needs a per-night
    # price in the guest's own currency for display. Payments doesn't
    # exist yet at this point in the flow (only created after form
    # submission below), so this can't come from a Payments row the way
    # check.html's post-payment receipt does -- computed fresh here instead.
    room_price_guest = (room_price_gbp * rate_guest).quantize(TWO_DP)
 
    subtotal_host = room_price_host * bookdays
    subtotal_gbp = room_price_gbp * bookdays
    subtotal_guest = subtotal_gbp * rate_guest
 
    # Import the voucher form
    payform = PaymentForm()
 
    # --------------------------------------------------------------
    # Discount -- computed in GBP first, then derived into host/guest
    # currency from that single canonical figure (same pattern as the
    # service charge in create_booking()).
    #
    # Deal (host-funded, percentage): reduces the host's actual earning.
    # Voucher (app-funded, flat GBP amount per policy): does NOT reduce
    # the host's earning -- the platform absorbs it. Recorded on
    # HostEarning as informational voucher_amount_*, not discount_*.
    # --------------------------------------------------------------
    voucher = None
    voucher_id = None
    discount_gbp = Decimal('0.00')
    discount_funded_by = None
 
    if book.deal:
        discount_gbp = subtotal_gbp * (Decimal(str(book.deal.discount_percent)) / 100)
        # AMENDED: was unconditionally 'host' for every deal. A deal with
        # room_id set is a genuine host-chosen discount on their own room
        # -- 'host' is correct there. A deal with room_id NULL is one of
        # the platform-wide campaigns (Weekend Deal, etc.), which can get
        # randomly paired with ANY room's listing on the homepage -- that
        # host never opted into it, so it shouldn't reduce their earning.
        discount_funded_by = 'host' if book.deal.room_id else 'app'
    else:
        voucher_id = session.get("voucher_id")
        if voucher_id:
            voucher = Vouchers.query.get(voucher_id)
            if voucher:
                existing_usage = VoucherUsage.query.filter_by(voucher_id=voucher.id,
                                                user_id=current_user.id).first()
                if not existing_usage:
                    discount_gbp = Decimal(str(voucher.value))  # already GBP, per policy
                    discount_funded_by = 'app'
            else:
                session.pop("voucher_id", None)
                voucher = None
 
    discount_host = (discount_gbp * rate_host).quantize(TWO_DP)
    discount_guest = (discount_gbp * rate_guest).quantize(TWO_DP)
    discount_gbp = discount_gbp.quantize(TWO_DP)
 
    total_paid_guest = max(subtotal_guest - discount_guest, Decimal('0.00')).quantize(TWO_DP)
    total_paid_gbp = max(subtotal_gbp - discount_gbp, Decimal('0.00')).quantize(TWO_DP)
 
    # check if a deal booking exists:
    deal_booking = book.deal is not None
    # --------------------------------
    # FORM PAYMENT
    # --------------------------------    
    if payform.validate_on_submit():
        # Transaction fee -- assumes fee_calculator operates on the
        # amount actually charged (guest currency) and returns a fee in
        # that same currency. Verify this matches fee_calculator's real
        # behavior before relying on it.
        transac_fee_guest = Decimal(str(fee_calculator(total_paid_guest)))
        transac_fee_gbp = (transac_fee_guest / rate_guest).quantize(TWO_DP)
        transac_fee_host = (transac_fee_gbp * rate_host).quantize(TWO_DP)
 
        # Loyalty points from the GBP-normalized total, not the
        # currency-varying total_paid -- otherwise the same stay is
        # worth wildly different points depending on the guest's currency.
        points = int(total_paid_gbp // 30)
 
        # Create payment record
        payment = Payments(
            pay_method=payform.pay_method.data, room_price_original=room_price_host,
            room_price_gbp=room_price_gbp.quantize(TWO_DP), room_price_currency=host_currency,
            room_price_exchange_rate=rate_host, book_days=bookdays,
            discount_host=discount_host, discount_gbp=discount_gbp,
            discount_funded_by=discount_funded_by, transac_fee_host=transac_fee_host,
            transac_fee_gbp=transac_fee_gbp, total_paid=total_paid_guest,
            payment_currency=guest_currency, payment_exchange_rate=rate_guest,
            accounting_currency='GBP', accounting_amount=total_paid_gbp,
            status='Paid', points_earned=points, user_id=current_user.id,
            booking_id=book.id, voucher_id=voucher.id if voucher else None,
            deal_id=book.deal_id if book.deal_id else None,
        )
        db.session.add(payment)
        # Award loyalty points
        current_user.rzerv_points = (current_user.rzerv_points or 0) + points
        
        db.session.flush()
 
        # Create hostearning record. Only a HOST-funded discount (deal)
        # reduces host_earning_*; an app-funded voucher is tracked
        # separately (voucher_amount_*) and does not reduce it.
        host_discount_host = discount_host if discount_funded_by == 'host' else Decimal('0.00')
        host_discount_gbp = discount_gbp if discount_funded_by == 'host' else Decimal('0.00')
        voucher_amount_host = discount_host if voucher else Decimal('0.00')
        voucher_amount_gbp = discount_gbp if voucher else Decimal('0.00')
 
        earning = HostEarning(
            user_id=book.rooms.user_id, booking_id=book.id, payment_id=payment.id,
            gross_amount_host=subtotal_host, gross_amount_gbp=subtotal_gbp.quantize(TWO_DP),
            host_currency=host_currency,exchange_rate=rate_host,
            discount_host=host_discount_host, discount_gbp=host_discount_gbp,
            voucher_amount_host=voucher_amount_host,voucher_amount_gbp=voucher_amount_gbp,
            platform_fee_host=transac_fee_host,platform_fee_gbp=transac_fee_gbp,
            host_earning_host=(subtotal_host - transac_fee_host - host_discount_host).quantize(TWO_DP),
            host_earning_gbp=(subtotal_gbp - transac_fee_gbp - host_discount_gbp).quantize(TWO_DP),
            # status left unset -- defaults to 'Pending' per the model
        )
        db.session.add(earning)
        # Update booking & room status
        book.status = 'Confirmed'
        book.active = True
        #room.status = 'Occupied'
        db.session.commit() 
        # Create voucher usage record
        if voucher:
            db.session.flush()
            usage = VoucherUsage(voucher_id=voucher.id, user_id=current_user.id,
                             payment_id=payment.id)
            db.session.add(usage)
            db.session.commit()
        
        return redirect(url_for('bedrooms.paysuccess', booking_id=book.id))
    # Pass text to submit button    
    payform.submit.label.text = f"Pay now {total_paid_guest} {guest_currency}"
    return render_template('pages/payment.html',  title='Checkout', 
                          room=room, room_id=room.id, book=book, discount=discount_guest,
                          subtotal=subtotal_guest, total_paid=total_paid_guest, payform=payform,
                          voucher_id=voucher_id, deal_booking=deal_booking,
                          room_price_guest=room_price_guest,
                          currency_symbol=get_symbol(guest_currency),
                          guest_currency=guest_currency)

# Voucher checker helper function 
@bedrooms.route("/check-voucher", methods=["POST"])
@login_required  # AMENDED: was commented out, but current_user.id is used unconditionally below -- would crash for an anonymous visitor
def checkvoucher():
    data = request.get_json(force=True)  
    
    if not data:
        return jsonify({
            "message": "❌ Invalid request format"
        })
    code = data.get("voucher_code", "").strip()
 
    if not code:
        return jsonify({
            "message": " ", #"❌ No voucher code provided"
            "discount": 0
        })
    voucher = Vouchers.query.filter_by(code=code).first()
    # invalid
    if not voucher:
        session.pop("voucher_id", None)
        return jsonify({"message": "<span style='color:red'>invalid code</span>"})
    
     # Check if CURRENT USER already used voucher
    existing_usage = VoucherUsage.query.filter_by(voucher_id=voucher.id,
                                                  user_id=current_user.id).first()
    if existing_usage:
        session.pop("voucher_id", None)
        return jsonify({
            "message":
            "<span style='color:red'>code already used</span>"})
 
    # AMENDED: was returning float(voucher.value) completely unconverted
    # -- voucher.value is GBP per policy, but this live preview needs to
    # match what checkout() actually charges, which converts vouchers
    # into the guest's own currency before applying them. Without this,
    # the number shown while typing a code didn't match what got charged
    # on submission.
    guest_currency = VisitorPreferences().currency
    rates = get_exchange_rates()
    raw_rate = rates.get(guest_currency)
 
    if raw_rate is None:
        return jsonify({
            "message": "<span style='color:red'>Voucher currently unavailable for your currency.</span>",
            "discount": 0
        })
 
    rate = Decimal(str(raw_rate))
    discount_gbp = Decimal(str(voucher.value))
    discount_guest = (discount_gbp * rate).quantize(Decimal('0.01'))
    # valid
    session["voucher_id"] = voucher.id
    session.modified = True

    # IMPORTANT DEBUG LINE (add this temporarily)
    #print("SESSION SET:", session.get("voucher_id"))
 
    return jsonify({"message": "<span style='color:green'>valid code, voucher applied</span>",
                    "discount": float(discount_guest)
                  })

# payment confirmation
@bedrooms.route("/paysuccess/<int:booking_id>", methods=['GET', 'POST']) 
@login_required
def paysuccess(booking_id):
    '''This function create a route to render payment confirmation page''' 
    # query the db about specific user reviews
    #room = Rooms.query.get_or_404(room_id)
    booking = ( Bookings.query
                .filter_by(id=booking_id)
                .first_or_404()
            )
    # payment = Payments.query.get_or_404(current_user.id)
    if booking:
        booking_confirm_email(booking, booking.id)
        flash(_(f'Link to view booking summary sent to {booking.pguest_email}'), 'success')
    else:
        flash(_('Server error, summary not sent, contact us now'), 'warning' )
  

    return render_template('pages/paysuccess.html',  title='Pay Success', 
                          booking=booking)

@bedrooms.route("/api/room/<int:room_id>/calendar")
def room_calendar(room_id):
    bookings = Bookings.query.filter_by(room_id=room_id,
                                        status="Confirmed").all()
    blocks = RoomBlock.query.filter_by(room_id=room_id).all()
    events = []

    # 🔴 BOOKINGS
    for b in bookings:
        events.append({
            "id": f"booking-{b.id}",
            "title": "Booked",
            "start": b.arrival.isoformat(),
            "end": b.departure.isoformat(),
            "extendedProps": {
                "type": "booking"
            }
        })

    # ⚫ BLOCKS
    for blk in blocks:
        events.append({
            "id": blk.id,
            "title": blk.reason or "Blocked",
            "start": blk.start_date.isoformat(),
            "end": blk.end_date.isoformat(),
            "extendedProps": {
                "type": "block",
                "reason": blk.reason or "Blocked"
            }
        })

    return jsonify(events)

# Create block dates (host action)
@bedrooms.route("/api/room/<int:room_id>/block", methods=["POST"])
@login_required
def block_dates(room_id):
    data = request.get_json()
    block = RoomBlock(room_id=room_id,
                start_date=datetime.strptime(data["start"], "%Y-%m-%d").date(),
                end_date=datetime.strptime(data["end"], "%Y-%m-%d").date(),
                reason=data.get("reason", "Blocked"),
                notes=data.get("notes")
            )
    db.session.add(block)
    db.session.commit()

    return jsonify({"success":True, "message": "Blocked successfully"})

# Unblock dates
@bedrooms.route( "/api/room/<int:room_id>/block/<int:block_id>", methods=["DELETE"])
@login_required
def unblock_dates(room_id, block_id):

    block = RoomBlock.query.filter_by(id=block_id, room_id=room_id).first_or_404()

    db.session.delete(block)
    db.session.commit()

    return jsonify({"success": True, 
                    "message": "Blocked dates removed successfully."
                  })

# Host calendar route
@bedrooms.route("/host/calendar/<int:room_id>")
@login_required
def host_calendar(room_id):
    room = Rooms.query.get_or_404(room_id)
    # optional security: only owner can view
    if room.user_id != current_user.id:
        abort(403)

    return render_template("udashpages/calendar.html", title='Calendar',
                         room=room, room_id=room.id)

@bedrooms.route("/roomdetail/<int:room_id>", methods=['GET', 'POST']) 
def roomdetail(room_id):
    '''This function create a route to render the room details page'''
    # fetch the room ads by id if exist or return 404 if doesnt
    room = Rooms.query.get_or_404(room_id)
    # Query someinfo from the db
    roominfo = Rooms.query.filter_by(id=room_id).first()
    roomextra = Roomextra.query.filter_by(id=room_id).first()

    # FIXED: was 3 separate queries (reviews, totalrev via .count(),
    # ratetot via a separate SUM query fed into get_total()) for numbers
    # all derivable from one already-fetched list. Also now filters to
    # Published only -- the original pulled every review regardless of
    # status, meaning a Flagged review still counted toward the public
    # average and still displayed.
    reviews = (Roomreviews.query
               .filter_by(room_id=room.id, status='Published')
               .order_by(Roomreviews.date_posted.desc())
               .all())
    totalrev = len(reviews)
    revscore = round(sum(r.rate_us for r in reviews) / totalrev, 1) if totalrev else 0

    # Log a view -- deduped per room per day (not per session forever),
    # since a trend chart needs a returning visitor next week to count
    # as a new data point, not be silently ignored.
    today_key = f"viewed_room_{room.id}_{date.today().isoformat()}"
    if not session.get(today_key):
        db.session.add(RoomView(room_id=room.id))
        session[today_key] = True
        db.session.commit()

    # Which of these reviews has the CURRENT viewer already marked
    # helpful? One query for the whole page, not one per review -- same
    # reasoning as everywhere else we've optimized this route.
    my_helpful_votes = set()
    if current_user.is_authenticated and reviews:
        review_ids = [r.id for r in reviews]
        my_helpful_votes = {
            v.review_id for v in ReviewHelpful.query.filter(
                ReviewHelpful.user_id == current_user.id,
                ReviewHelpful.review_id.in_(review_ids),
            ).all()
        }

    # create room reviews form
    form = RoomReviewsForm()

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash(_('Please, login or register to review this room!'), 'danger')
            return redirect(url_for('users.login'))

        # Find a completed, not-yet-reviewed booking by this user for this
        # room -- this is the app-layer check the DB's FK can't do on its
        # own (verifying the booking actually belongs to this user/room).
        eligible_booking = (
            Bookings.query
            .outerjoin(Roomreviews, Roomreviews.booking_id == Bookings.id)
            .filter(
                Bookings.user_id == current_user.id,
                Bookings.room_id == room.id,
                Bookings.departure < datetime.utcnow().date(),
                Roomreviews.id.is_(None),  # excludes bookings already reviewed
            ).order_by(Bookings.departure.desc()).first())

        if eligible_booking is None:
            flash(_("You can only review a room after a completed stay, and each stay can only be reviewed once."), 'warning')
            return redirect(url_for('bedrooms.roomdetail', room_id=room.id))

        clean_msg = sanitize_input(form.message.data)
        review = Roomreviews(rate_us=form.rate_us.data, message=clean_msg, room_id=room.id,
                            user_id=current_user.id, booking_id=eligible_booking.id)
        db.session.add(review)
        db.session.commit()

        flash(_('Your review has been submitted successfully!'), 'success')
        return redirect(url_for('bedrooms.roomdetail', room_id=room.id))

    return render_template('pages/roomdetails.html', title='Room Details', 
                           roominfo=roominfo, roomextra=roomextra, form=form, room=room,
                           totalrev=totalrev, reviews=reviews, revscore=revscore,
                           my_helpful_votes=my_helpful_votes)

@bedrooms.route("/roomextra/<int:room_id>", methods=['GET', 'POST']) 
@login_required
def roomextra(room_id):
    '''This function create a route to render room extra form page'''
    # fetch the room ads by id if exist or return 404 if doesnt
    room = Rooms.query.get_or_404(room_id)
    # Check if the user is the author of the post first 
    if room.user_id != current_user.id:
        abort(403)
    # Create an instance of room form
    form = RoomExtraForm()

    if form.validate_on_submit():
        # room listing info   
        room_extra = Roomextra(sleeping=form.sleeping.data, hot_water=form.hot_water.data,
                        tv=form.tv.data, internet=form.internet.data, kitchen=form.kitchen.data, 
                        towels=form.towels.data, resto=form.resto.data, bar=form.bar.data, 
                        spa=form.spa.data, car=form.car.data, shop=form.shop.data, 
                        concierge=form.concierge.data, aircon=form.aircon.data, pool=form.pool.data,
                        workspace=form.workspace.data, washing=form.washing.data, sport=form.sport.data,
                        parking=form.parkin.data, room_id=room.id)

        db.session.add(room_extra)                                          # adding data to the database
        db.session.commit()                                                 # saving the changes                                                               
        flash(
            _(f"Your room extra has been added successfully.", 'success')
            )   # display validation message 

        return redirect(url_for('udash.mylistings', room_id=room.id))
    
    return render_template('udashpages/amenities.html',  title='Room Amenities', form=form)

# To update existing room
@bedrooms.route("/room/update/<int:room_id>", methods=['GET', 'POST'])
@login_required
def update_room(room_id):
    '''This function a create a route to update a post'''
    # fetch the room ads by id if exist or return 404 if doesnt 
    room = Rooms.query.get_or_404(room_id)
    userads = Rooms.query.filter_by(user_id=current_user.id).all()
    # Check if the user is the author of the post first 
    if room.user_id != current_user.id:
        abort(403)
    # Create an instance of room form
    form = UpdateRoomForm()
 
    # adding the logic to validate changes and add to db
    if form.validate_on_submit(): 
        room.room_name = form.room_name.data
        room.room_category = form.room_category.data
        room.short_desc = form.short_desc.data
        room.max_occupancy = form.max_occupancy.data
        room.price = form.price.data
        room.description = form.description.data
        room.status = form.status.data
        room.rule1 = form.rule1.data
        room.rule2 = form.rule2.data
        room.rule3 = form.rule3.data

        # NEW: find-or-create the room's own linked Deals row for its
        # host-set discount. If one already exists, update it in place
        # rather than creating a second (room_id is unique=True on
        # Deals, so a second insert would fail anyway). Clearing the
        # field to 0/blank deactivates rather than deletes it, keeping
        # the row (and its history) rather than losing it outright.
        existing_deal = Deals.query.filter_by(room_id=room.id).first()
        if form.discount_percent.data:
            if existing_deal:
                existing_deal.discount_percent = form.discount_percent.data
                existing_deal.active = True
            else:
                db.session.add(Deals(room_id=room.id, discount_percent=form.discount_percent.data, active=True))
        elif existing_deal:
            existing_deal.active = False
 
        # Save changes
        db.session.commit()
        flash(_('Room details has been successfully updated!'), 'success')
        return redirect(url_for('udash.mylistings', room_id=room.id))
 
    elif request.method == 'GET':
        # Populate the post with the content and tilte of post to update 
        form.room_name.data = room.room_name
        form.room_category.data = room.room_category
        form.short_desc.data = room.short_desc
        form.max_occupancy.data = room.max_occupancy
        form.price.data = room.price
        form.description.data = room.description
        form.status.data = room.status
        form.rule1.data = room.rule1  # FIXED: was form.usp1.data = room.usp1 -- neither field exists on either side, crashed this route on every GET
        form.rule2.data = room.rule2  # FIXED: was form.usp2.data = room.usp2
        form.rule3.data = room.rule3  # FIXED: was form.usp3.data = room.usp3
 
        active_deal = get_room_active_deal(room.id)
        if active_deal:
            form.discount_percent.data = active_deal.discount_percent 
        #####
    return render_template('udashpages/roomupdate.html',  title='Listing Update', form=form)

# To update existing room
@bedrooms.route("/update_roompics/<int:room_id>", methods=['GET', 'POST'])
@login_required
def update_roompics(room_id):
    '''This function a create a route to update room images'''
    # fetch the post by id if exist or return 404 if doesnt 
    room = Rooms.query.get_or_404(room_id)
    # Check if the user is the author of the post first 
    if room.user_id != current_user.id:
        abort(403)
    # Create an instance of room form
    form = UpdateRoomPictureForm()
    # adding the logic to validate changes and add to db
    if form.validate_on_submit():
        # AMENDED: was resetting ALL 6 slots to the default image on
        # every submission, then refilling only as many as were just
        # uploaded -- meaning any partial update (e.g. replacing just
        # one photo) silently destroyed the other 5 real images. Now
        # only touches a slot when that specific field actually received
        # a new upload; everything else is left completely untouched.
        image_fields = [
            'image1',
            'image2',
            'image3',
            'image4',
            'image5',
            'image6'
        ]
 
        updated_any = False
        for field_name in image_fields:
            file = getattr(form, field_name).data
            if file and file.filename != '':
                filename = save_picture(file)
                setattr(room, field_name, filename)
                updated_any = True
 
        if updated_any:
            db.session.commit()
            flash(_('Room images successfully updated!'), 'success')
        else:
            flash(_('No new images were selected.'), 'info')
 
        return redirect(url_for('udash.mylistings', room_id=room.id))
    
    return render_template('udashpages/picsupdate.html',  title='Room Images', 
                            form=form, room=room)

# route to delete a specific listing
@bedrooms.route("/room/<int:room_id>/delete", methods=['GET', 'POST'])
@login_required
def delete_room(room_id):
    '''This function enable to delete a post'''
    # fetch the room by id if exist or return 404 if doesnt 
    room = Rooms.query.get_or_404(room_id)
    # Check if the user is the creator of the room first 
    if room.user_id != current_user.id:
        abort(403)
    # delete the post in the db and commit the change
    db.session.delete(room)
    db.session.commit()
    # Display an update message to the user 
    flash(_('Your listing has been successfully deleted!'), 'success')
    return redirect(url_for('users.listings', room_id=room.id))

@bedrooms.route("/review/<int:review_id>/helpful", methods=['POST'])
@login_required
def toggle_helpful(review_id):
    review = Roomreviews.query.get_or_404(review_id)

    if review.user_id == current_user.id:
        return jsonify(error="You can't vote on your own review."), 403

    existing = ReviewHelpful.query.filter_by(review_id=review_id, user_id=current_user.id).first()

    if existing:
        # Un-vote
        db.session.delete(existing)
        review.helpful_count = max(0, review.helpful_count - 1)
        voted = False
    else:
        db.session.add(ReviewHelpful(review_id=review_id, user_id=current_user.id))
        review.helpful_count += 1
        voted = True

    db.session.commit()
    return jsonify(voted=voted, count=review.helpful_count)
#=====================================================================