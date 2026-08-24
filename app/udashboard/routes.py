from flask import (Blueprint, render_template, flash, redirect, url_for, 
                   request, abort, jsonify)
from flask_login import current_user, login_required
from app import db
from app.models.usermodel import User
from app.models.roommodel import Rooms, Roomreviews, GuestReviews, RoomView, Deals
from app.models.bookmodel import Bookings, HostEarning, Withdrawal, Refund
from app.models.chatmodel import Message, Conversation 
from ..users.forms import (UpdateAccountForm)
from app.rooms.forms import AddRoomForm, WithdrawalForm, GuestReviewForm
# from ..users.usermails.resetrequest import send_reset_email
# from ..users.usermails.joinusmail import member_regismail
from ..users.utils import save_picture
from app.services.location_service import get_location
from app.services.preference_service import VisitorPreferences
from ..rooms.roomutils import sanitize_input, can_cancel, current_date
from flask_socketio import (SocketIO, emit, join_room, leave_room)
from app import socketio
from datetime import datetime, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract
import geopandas as gpd
from shapely.geometry import Point
from app.helpers.chat_security import check_message
from app.helpers.earnings_change import calculate_monthly_earnings_change
from app.helpers.host_balance import get_host_balance
from app.helpers.format_datime import format_message_time
from app.helpers.email_verify import email_verified_required
from app.helpers.room_stats import get_daily_view_counts
from app.services.currency import convert_currency, COUNTRY_CURRENCY, get_exchange_rates, format_room_price
from flask_babel import _

udash = Blueprint('udash', __name__)

# Fetch monthly earnings
@udash.route("/host/earnings-chart")
@login_required
def host_earnings_chart():
    today = datetime.today()
    months = []
    earnings = []
 
    # Last 12 months
    for i in range(11, -1, -1):
        month_date = today - relativedelta(months=i)
 
        year = month_date.year
        month = month_date.month
 
        # AMENDED: converting each month's GBP total into the host's own
        # preferred_currency before it reaches the chart. Using
        # convert_currency (returns a plain number), not
        # convert_and_format (returns a formatted string like "£1,234")
        # -- Chart.js needs raw numbers to plot, not currency-symbol text.
        total = db.session.query(db.func.sum(HostEarning.host_earning_gbp)
        ).filter(HostEarning.user_id == current_user.id,
            extract('year', HostEarning.created_at) == year,
            extract('month', HostEarning.created_at) == month).scalar() or 0
        total = convert_currency(float(total), "GBP", current_user.preferred_currency)
 
        months.append( month_date.strftime("%b"))
        earnings.append(float(total))
 
    return jsonify({"labels": months, "values": earnings})
 
# Top three most performing room
@udash.route("/host/top-rooms-revenue")
@login_required
def top_rooms_revenue():
 
    # host_earning_gbp, not host_earning_host: even though grouping by
    # Rooms.id keeps each room's own sum currency-consistent, the
    # total_revenue and percentage-of-total calculated below combine
    # figures across DIFFERENT rooms -- if two rooms are priced in
    # different currencies, adding their raw host-currency revenue
    # together before computing percentages would still be wrong, even
    # though each room's individual row would look fine in isolation.
    results = db.session.query(Rooms.room_name, db.func.sum(
            HostEarning.host_earning_gbp).label("revenue"), db.func.count(
            Bookings.id).label("booking_count")).join(
            Bookings, HostEarning.booking_id == Bookings.id
            ).join(Rooms, Bookings.room_id == Rooms.id).filter(
            HostEarning.user_id == current_user.id).group_by(
            Rooms.id, Rooms.room_name).order_by(db.desc("revenue")
                                                ).limit(3).all()
 
    # Calculate total revenue
    total_revenue = sum(float(row.revenue)
                        for row in results)
    rooms = []
 
    for room, revenue, booking_count in results:
        revenue = float(revenue)
        percentage = 0
 
        if total_revenue > 0:
            percentage = round((revenue / total_revenue) * 100, 1)
 
        # AMENDED: percentage is computed above from the raw GBP figures
        # (a ratio is unaffected by which currency it's expressed in, so
        # this stays correct regardless of conversion). Only the display
        # value itself is converted, and only after the ratio math is done.
        revenue = convert_currency(revenue, "GBP", current_user.preferred_currency)
 
        rooms.append({"room": room, "revenue": revenue,
                        "percentage": percentage, 
                        "booking_count": booking_count,
                    })
 
    return jsonify(rooms)
     
# Room locations in world map user specific
@udash.route("/host/room-locations")
@login_required
def room_locations():
    rooms = Rooms.query.filter_by(user_id=current_user.id).all()
 
    return jsonify([
        {
            "name":room.room_name,
            "city":room.room_location,
            "price":room.price,
            "country":room.room_country,
            "lat":room.latitude,
            "lng":room.longitude
        }
        for room in rooms
    ])

# public 
@udash.route("/rooms/map-locations")
@login_required
def room_map_locations():
    rooms = Rooms.query.filter(Rooms.status=="Available").all()
    #rooms = Rooms.query.all()
 
    data=[]
 
    for room in rooms:
        data.append({
            "id": room.id,
            "name": room.room_name,
            "city": room.room_location,
            "price": room.price,
            "price_display": format_room_price(room),  # NEW: converted to the current viewer's currency, formatted with the correct symbol -- the raw "price" field above was being shown with a hardcoded £ regardless of the room's actual currency
            "country": room.room_country,
            "lat": room.latitude,
            "lng": room.longitude
        })
 
    return jsonify(data)

# Router with Map using Geopanda
@udash.route("/api/map/rooms")
def room_map_data():
    rooms = Rooms.query.filter(Rooms.status=="Available").all()

    features = []

    for room in rooms:
        features.append({
            "type": "Feature",
            "properties": {
                "id": room.id,
                "name": room.room_name,
                "city": room.room_location,
                "price": room.price,
                "price_display": format_room_price(room),  # NEW: same fix as the other map route
                "image": room.image1,
                "url": url_for("bedrooms.roomdetail", room_id=room.id)
            },
            "geometry": {
                "type": "Point",
                "coordinates": [room.longitude, room.latitude]
            }
        })

    return jsonify({"type":"FeatureCollection", "features":features })

# =========================================================================================


@udash.route("/request-withdrawal", methods=["POST"])
@login_required
def request_withdrawal():
    form = WithdrawalForm()
 
    if form.validate_on_submit():
        amount = form.amount.data
 
        # AMENDED: get_host_balance() now returns a GBP figure (see
        # host_balance.py), but `amount` is still entered in the host's
        # own currency -- comparing them directly would silently compare
        # two different currencies as if they were the same number. The
        # rate lookup + GBP conversion has to happen BEFORE the balance
        # check now, not after it.
        rates = get_exchange_rates()
        host_currency = current_user.preferred_currency
        raw_rate = rates.get(host_currency)
 
        if raw_rate is None:
            flash(_("Withdrawal currently unavailable: missing exchange rate for %(currency)s.", currency=host_currency), "danger")
            return redirect(url_for("udash.earnings"))
 
        rate = Decimal(str(raw_rate))
        amount_host = Decimal(str(amount))
        amount_gbp = (amount_host / rate).quantize(Decimal('0.01'))
 
        balance = get_host_balance(current_user.id)  # GBP
 
        if amount_gbp > balance:
            flash(_("Insufficient balance"),"danger")
 
            return redirect(url_for("udash.earnings"))
 
        withdrawal = Withdrawal(
            user_id=current_user.id,
            amount_host=amount_host,
            amount_gbp=amount_gbp,
            host_currency=host_currency,
            withdraw_xchange_rate=rate,
            status="Pending",
        )
 
        db.session.add(withdrawal)
        db.session.commit()
 
        flash(_("Withdrawal request submitted"), "success")
    return redirect(url_for("udash.earnings"))
 
@udash.route("/udashboard", methods=['GET', 'POST']) 
@login_required
def udashboard():
    '''This function create a route to render user dashboard page''' 
    # find the user total listing
    totrooms = db.session.query(Rooms).filter(Rooms.user_id==current_user.id).count()
    # FIXED: was counting every booking regardless of status --
    # including Pending ones where the guest never actually completed
    # payment (abandoned mid-checkout). Only Confirmed bookings should
    # count toward this headline stat.
    totbook = Bookings.query.join(Rooms).filter(
        Rooms.user_id == current_user.id,
        Bookings.status == "Confirmed"
    ).count()
    
    # host_earning_gbp -- dashboard headline figure, same cross-currency
    # aggregation reasoning as the other two fixes in this file.
    total_earnings = db.session.query(db.func.sum(HostEarning.host_earning_gbp)
                                    ).filter(HostEarning.user_id == current_user.id,
                                            HostEarning.status == "Approved"
                                             ).scalar() or 0
    # AMENDED: convert the GBP total into the host's preferred currency.
    # Kept as a plain number (not convert_and_format's formatted string)
    # so any existing numeric formatting/comparisons in the template
    # keep working -- pass current_user.preferred_currency to the
    # template too if you want the currency code/symbol shown alongside it.
    total_earnings = convert_currency(float(total_earnings), "GBP", current_user.preferred_currency)
    
    # amount_gbp, not amount_host -- same cross-currency aggregation
    # reasoning as total_earnings above. Withdrawal.amount was never a
    # real column; it was split into amount_host/amount_gbp when that
    # model was fixed.
    total_withdrawals = db.session.query(db.func.sum(Withdrawal.amount_gbp)
                                        ).filter(Withdrawal.user_id==current_user.id,
                                        Withdrawal.status.in_(["Pending","Approved"]
                                        )).scalar() or 0
    # Converted to the host's preferred currency for display, matching
    # total_earnings' treatment -- kept as a plain number, not a
    # formatted string.
    total_withdrawals = convert_currency(float(total_withdrawals), "GBP", current_user.preferred_currency)
    
    # available_balance = get_host_balance(current_user.id) 
    earnings_state = calculate_monthly_earnings_change(current_user.id)
 
    return render_template('udashpages/dashboard.html',  title='User Dashboard',
                            totbook=totbook,totrooms=totrooms, 
                            total_earnings=total_earnings, earnings_state=earnings_state, 
                            total_withdrawals=total_withdrawals)

@udash.route("/profile", methods=['GET', 'POST'])
@login_required 
def profile():
    '''This function create a route to render user profile page''' 
    
    form = UpdateAccountForm()
    
    if form.validate_on_submit():
        if form.picture.data:    # check if profile picture has been uploaded
            picture_file = save_picture(form.picture.data)
            # set the profile image file
            current_user.image_file = picture_file
        # allow update if username & email is valid
        current_user.company_name = form.company_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        # current_user.first_name = form.first_name.data
        # current_user.last_name = form.last_name.data
        current_user.gender = form.gender.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.city = form.city.data
        current_user.country = form.country.data
        current_user.zip_code = form.zip_code.data
        current_user.aboutme = form.aboutme.data
       
        # save the db entry
        db.session.commit()
        # Displaying an update message
        flash(_('Your profile has been successfully updated'), 'success')
        # redirect after update to the account page
        return redirect(url_for('udash.profile'))
    # populate the form field with the user data
    elif request.method == 'GET':
        form.company_name.data =  current_user.company_name 
        form.username.data = current_user.username
        form.email.data = current_user.email
        # form.first_name.data = current_user.first_name
        # form.last_name.data = current_user.last_name
        form.gender.data = current_user.gender
        form.phone.data = current_user.phone
        form.address.data = current_user.address
        form.city.data = current_user.city
        form.country.data = current_user.country
        form.zip_code.data = current_user.zip_code
        form.aboutme.data = current_user.aboutme
            
    # set cuurent user profile pictures to pass to the current default image
    image_file = url_for('static', filename='userpics/profile/' + current_user.image_file) 
        
    return render_template('udashpages/usprofile.html', title='My Profile', image_file=image_file, 
                           form=form)

@udash.route("/mybookings", methods=['GET', 'POST']) 
@login_required
def mybookings():
    '''This function create a route to render user bookings page''' 
    guest_page = request.args.get('guest_page', 1, type=int)
    host_page = request.args.get('host_page', 1, type=int)

    bookguest = (Bookings.query.filter(Bookings.user_id == current_user.id,
                                    Bookings.status != 'Expired'  # NEW: expired/abandoned bookings stay in the DB for audit (BookAdmin still shows them unfiltered), but shouldn't clutter the guest's own active bookings list
                                    ).options(
                                    db.joinedload(Bookings.conversation))
                                    .order_by(Bookings.created_at.desc())
                                    .paginate(page=guest_page,
                                              per_page=4, error_out=False))
    
    bookhost = (Bookings.query.join(Rooms).filter(
                        Rooms.user_id == current_user.id,
                        Bookings.status != 'Expired'  # NEW: same reasoning as the guest-side filter above
                        ).options(db.joinedload(Bookings.conversation))
                        .order_by(Bookings.created_at.desc()
                        ).paginate(page=host_page, per_page=4, error_out=False))
    
    today = current_date()

    return render_template('udashpages/mybookings.html',  title='My Bookings', bookguest=bookguest,
                            bookhost=bookhost, today=today, can_cancel=can_cancel)

@udash.route("/earnings") 
@login_required
def earnings():
    '''This function create a route to render host earnings page''' 
   # page = request.args.get('page', 1, type=int)
    withd_page = request.args.get('guest_page', 1, type=int)
    earn_page = request.args.get('host_page', 1, type=int)
    form = WithdrawalForm()
 
    available_balance = get_host_balance(current_user.id)
    # AMENDED: get_host_balance() now returns GBP (see host_balance.py).
    # Converting to the host's own currency for display here, same
    # pattern as udashboard()'s total_earnings -- kept as a plain number
    # so the template's existing formatting/comparisons keep working.
    available_balance = convert_currency(float(available_balance), "GBP", current_user.preferred_currency)
 
    withdrawal = db.session.query(Withdrawal).filter(
                        Withdrawal.user_id==current_user.id
                        ).order_by(Withdrawal.requested_at.desc()
                                   ).paginate(page=withd_page, 
                                              per_page=3, 
                                              error_out=False)
 
    host_earning = HostEarning.query.filter_by(
                                            user_id=current_user.id
                                            ).order_by(HostEarning.created_at.desc()
                                            ).paginate(page=earn_page, 
                                              per_page=4, error_out=False)
    
    return render_template('udashpages/myearnings.html',  title='My Earnings', 
                          host_earning=host_earning, form=form, withdrawal=withdrawal,
                          available_balance=available_balance)

@udash.route("/refunds") 
@login_required
def refunds():
    '''This function create a route to render user payment page''' 
    page = request.args.get('page', 1, type=int)
    user_refund = Refund.query.filter_by(user_id=current_user.id
                                        ).order_by(Refund.created_at.desc()
                                        ).paginate(page=page, 
                                            per_page=3, 
                                            error_out=False)
    
    return render_template('udashpages/myrefund.html',  title='My Refund', 
                          user_refund=user_refund )

@udash.route("/myreviews") 
@login_required
def myreviews():
    '''This function create a route to render user reviews page''' 
    # query the db about specific user reviews
    myrevs = db.session.query(Roomreviews).filter(Roomreviews.user_id==current_user.id).all()

    return render_template('udashpages/reviews.html',  title='Reviews', myrevs=myrevs)

@udash.route("/rate-guest/<int:booking_id>", methods=['POST'])
@login_required
def rate_guest(booking_id):
    booking = Bookings.query.get_or_404(booking_id)

    # Security: only the actual host of this specific booking may review
    # this guest -- mirrors the ownership check in roomdetail()'s review
    # eligibility, just checking the host side instead of the guest side.
    if booking.rooms.user_id != current_user.id:
        abort(403)

    # Must be a genuinely completed stay -- same reasoning as guest
    # reviews requiring a departed booking, not just any booking.
    if booking.status != 'Confirmed' or booking.departure > date.today():
        flash(_("You can only rate a guest after their stay has completed."), "warning")
        return redirect(url_for('udash.mybookings'))  # adjust to your actual host-bookings route name

    # One review per stay -- booking_id is unique=True on GuestReviews,
    # but checking first gives a friendly message instead of a raw
    # IntegrityError if someone double-submits.
    existing = GuestReviews.query.filter_by(booking_id=booking.id).first()
    if existing:
        flash(_("You've already rated this guest for this stay."), "info")
        return redirect(url_for('udash.mybookings'))

    form = GuestReviewForm()

    if form.validate_on_submit():
        clean_msg = sanitize_input(form.message.data)
        review = GuestReviews(
            booking_id=booking.id,
            host_id=current_user.id,
            guest_id=booking.user_id,
            rate_us=form.rate_us.data,
            message=clean_msg,
        )
        db.session.add(review)
        db.session.commit()

        flash(_("Thanks -- your review of the guest has been submitted."), "success")
    else:
        flash(_("Rating and a review of at least 20 characters are required."), "warning")

    return redirect(url_for('udash.mybookings'))

@udash.route("/api/guest-reviews/<int:guest_id>")
@login_required
def api_guest_reviews(guest_id):
    ''' Returns published reviews for a given guest as JSON, for the
        view-reviews modal. Not restricted to hosts specifically -- review
        content itself isn't sensitive (mirrors how Roomreviews are already
        publicly visible on room pages), just requires being logged in.
    '''
    reviews = (GuestReviews.query
               .filter_by(guest_id=guest_id, status='Published')
               .order_by(GuestReviews.date_posted.desc())
               .all())

    return jsonify([
                    {"rate_us": r.rate_us,
                     "message": r.message,
                     "date_posted": r.date_posted.strftime("%d %b %Y"),
                     "host": r.host.username if r.host else "Host",
                    }
                    for r in reviews
                ])

@udash.route("/mylistings", methods=['GET', 'POST']) 
@login_required
@email_verified_required
def mylistings():
    '''This function create a route to render user listings page''' 
    page = request.args.get('page', 1, type=int)   
    form = AddRoomForm()
 
    roomlist = db.session.query(Rooms).filter(Rooms.user_id==current_user.id
                                              ).order_by(Rooms.created_at.desc()
                                                ).paginate(page=page, 
                                                    per_page=6, error_out=False)
 
    if form.validate_on_submit():
        # Get the location coordinate
        location = get_location(form.room_location.data)
 
        if not location:
            flash("Unable to locate this city.", "danger")
            return redirect(url_for("udash.mylistings"))
    
        if current_user.address and current_user.phone and current_user.zip_code != 'Change me':  
            clean_short_desc = sanitize_input(form.short_desc.data)
            clean_description = sanitize_input(form.description.data)
            # room listing info   
            room_info = Rooms(room_name=form.room_name.data, room_location=form.room_location.data,
                            borough=form.borough.data,
                            content_language=VisitorPreferences().language,  # NEW: language the host is browsing in at the moment they write this listing
                            room_country=location["country"], price=form.price.data, 
                            room_category=form.room_category.data, status=form.status.data,
                            short_desc=clean_short_desc, room_size=form.room_size.data, max_occupancy=form.max_occupancy.data, 
                            description=clean_description, rule1=form.rule1.data, rule2=form.rule2.data, rule3=form.rule3.data,
                            latitude=location["latitude"], longitude=location["longitude"],
                            user_id=current_user.id,
                            room_currency=COUNTRY_CURRENCY.get(location["country_code"], "GBP"))  # FIXED: was location["country"] (full name, e.g. "Côte d'Ivoire") against a dict keyed by 2-letter codes -- always silently fell back to GBP regardless of actual country
 
            db.session.add(room_info)                                                               # adding the user to the database
            db.session.flush()  # need room_info.id before creating the linked Deals row
 
            # NEW: host-set discount, stored as a Deals row linked to
            # this specific room (Option B -- Deals.room_id NULL stays
            # reserved for the 3 existing platform-wide campaigns).
            if form.discount_percent.data:
                deal = Deals(room_id=room_info.id, discount_percent=form.discount_percent.data, active=True)
                db.session.add(deal)
 
            db.session.commit()                                                                # saving the changes                                                               
            flash(_('Great! your room listing is now live.'), 'success')     # display validation message [ f'Account created for {form.username.data}!' ]
            # send account verification email to user
            #adslive_msg(user)
 
            return redirect(url_for('udash.mylistings'))
        else:
            flash(_('You need to fully complete your profile before you can make a room listing!'), 'warning')
    
    return render_template('udashpages/mylistings.html',  title='Listings', form=form,
                            roomlist=roomlist)

@udash.route("/room/<int:room_id>/stats")
@login_required
def room_stats(room_id):
    room = Rooms.query.get_or_404(room_id)

    # Host-only -- same ownership check pattern used everywhere else a
    # host looks at data tied to one of their own rooms.
    if room.user_id != current_user.id:
        abort(403)

    total_views = RoomView.query.filter_by(room_id=room_id).count()

    # Both fetched now, not on-demand -- toggling Week/Month in the UI
    # just swaps which already-loaded dataset the chart displays,
    # no round-trip needed.
    week_data = get_daily_view_counts(room_id, 7)
    month_data = get_daily_view_counts(room_id, 30)

    return render_template( 'udashpages/room_stats.html', title='Room Stats', 
                            room=room, total_views=total_views, week_data=week_data,
                            month_data=month_data)

# Join chat 
# @socketio.on("join")
# def handle_join(data):
#     conversation_id = data["conversation_id"]
#     conversation = Conversation.query.get(conversation_id)

#     if current_user.id == conversation.host_id:
#         other_user = User.query.get(conversation.guest_id)
#     else:
#         other_user = User.query.get(conversation.host_id)
#      # EVERYONE joins room
#     join_room(str(conversation_id))
#     # EVERYONE receives chat header
#     emit(
#         "chat_user",
#         {
#             "username": other_user.username,
#             "image": other_user.image_file
#         }
#     )

# # send message on chat 
# @socketio.on("send_message")
# def handle_send_message(data):
#     conversation_id = data["conversation_id"]
#     body = data["body"]

#     # ==================================
#     # CHECK MESSAGE SECURITY
#     # ==================================
#     security = check_message(body)
#     # ==================================
#     # FIND CONVERSATION
#     # ==================================
#     conversation = Conversation.query.get(conversation_id)

#     if not conversation:
#         return
#     # ==================================
#     # FIND RECEIVER
#     # ==================================
#     if current_user.id == conversation.host_id:
#         receiver_id = conversation.guest_id
#     else:
#         receiver_id = conversation.host_id
#     # ==================================
#     # CREATE MESSAGE
#     # ==================================
#     message = Message(
#         conversation_id=conversation_id, sender_id=current_user.id, 
#         receiver_id=receiver_id, body=body, is_read=False, is_flagged=False)
#     # ==================================
#     # FLAG SUSPICIOUS CONTENT
#     # ==================================
#     if security["flagged"]:
#         message.is_flagged = True
#         message.flag_reason = (",".join(security["words"]))
#     # ==================================
#     # SAVE MESSAGE
#     # ==================================
#     db.session.add(message)
#     db.session.commit()
#     # ==================================
#     # SEND MESSAGE TO CHAT ROOM
#     # ==================================
#     message_data = {
#         "sender_id": current_user.id,
#         "user": current_user.username,
#         "body": body,
#         "created_at": format_message_time(message.created_at),
#         "flagged": message.is_flagged
#     }
#     emit("receive_message",
#         message_data,
#         room=str(conversation_id))
#     # ==================================
#     # SEND WARNING TO SENDER
#     # ==================================
#     if security["flagged"]:
#         emit(
#             "chat_warning",
#             {"message":
#             "For your protection, please keep payments and contact exchanges inside our platform."
#             },
#             room=request.sid)
#     # ==================================
#     # UPDATE RECEIVER NOTIFICATION
#     # ==================================
#     unread = Message.query.filter(
#         Message.receiver_id == receiver_id,
#         Message.is_read == False).count()
#     emit("new_notification",
#         {
#             "count": unread
#         },
#         room=f"user_{receiver_id}"
#     )

# Join chat 
@socketio.on("join")
def handle_join(data):
    if not current_user.is_authenticated:
        return  # refuse silently -- no error detail handed to an unauthenticated caller

    conversation_id = data.get("conversation_id")
    conversation = Conversation.query.get(conversation_id)

    if not conversation:
        return

    # CRITICAL: only the two actual participants may join this room.
    # Without this check, any user could join any conversation's room by
    # guessing/enumerating conversation_id and silently read every message
    # broadcast to it.
    if current_user.id not in (conversation.guest_id, conversation.host_id):
        return

    if current_user.id == conversation.host_id:
        other_user = User.query.get(conversation.guest_id)
    else:
        other_user = User.query.get(conversation.host_id)

    join_room(str(conversation_id))
    emit(
        "chat_user",
        {
            "username": other_user.username,
            "image": other_user.image_file
        }
    )

# send message on chat 
@socketio.on("send_message")
def handle_send_message(data):
    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")
    raw_body = data.get("body", "")

    # ==================================
    # FIND CONVERSATION
    # ==================================
    conversation = Conversation.query.get(conversation_id)

    if not conversation:
        return

    # CRITICAL: only the two actual participants may send into this
    # conversation. Without this, any logged-in user could inject a
    # message into a conversation between two unrelated people.
    if current_user.id not in (conversation.guest_id, conversation.host_id):
        return

    # ==================================
    # SANITIZE -- separate concern from check_message() below, which
    # flags suspicious *content* (e.g. phone numbers), not markup/scripts.
    # ==================================
    body = sanitize_input(raw_body)
    if not body.strip():
        return  # don't save empty/whitespace-only messages

    # ==================================
    # CHECK MESSAGE SECURITY
    # ==================================
    security = check_message(body)
    # ==================================
    # FIND RECEIVER
    # ==================================
    if current_user.id == conversation.host_id:
        receiver_id = conversation.guest_id
    else:
        receiver_id = conversation.host_id
    # ==================================
    # CREATE MESSAGE
    # ==================================
    message = Message(
        conversation_id=conversation_id, sender_id=current_user.id, 
        receiver_id=receiver_id, body=body, is_read=False, is_flagged=False)
    # ==================================
    # FLAG SUSPICIOUS CONTENT
    # ==================================
    if security["flagged"]:
        message.is_flagged = True
        message.flag_reason = (",".join(security["words"]))
    # ==================================
    # SAVE MESSAGE
    # ==================================
    db.session.add(message)
    db.session.commit()
    # ==================================
    # SEND MESSAGE TO CHAT ROOM
    # ==================================
    message_data = {
        "sender_id": current_user.id,
        "user": current_user.username,
        "body": body,
        "created_at": format_message_time(message.created_at),
        "flagged": message.is_flagged
    }
    emit("receive_message",
        message_data,
        room=str(conversation_id))
    # ==================================
    # SEND WARNING TO SENDER
    # ==================================
    if security["flagged"]:
        emit(
            "chat_warning",
            {"message":
            "For your protection, please keep payments and contact exchanges inside our platform."
            },
            room=request.sid)
    # ==================================
    # UPDATE RECEIVER NOTIFICATION
    # ==================================
    unread = Message.query.filter(
        Message.receiver_id == receiver_id,
        Message.is_read == False).count()
    emit("new_notification",
        {
            "count": unread
        },
        room=f"user_{receiver_id}"
    )

# @udash.route("/conversation/<int:id>/messages")
# @login_required
# def get_messages(id):
#     messages = Message.query.filter_by(conversation_id=id
#                                       ).order_by(Message.created_at
#                                                 ).all()

#     return jsonify([
#         {
#             "sender_id": msg.sender_id,
#             "user": User.query.get(msg.sender_id).username,
#             "body": msg.body,
#             "created_at": format_message_time(msg.created_at)
#         }
#         for msg in messages
#     ])

@udash.route("/conversation/<int:id>/messages")
@login_required
def get_messages(id):
    conversation = Conversation.query.get(id)
 
    if not conversation:
        abort(404)
 
    # Same check as the socket handlers -- @login_required alone doesn't
    # confirm this user actually belongs to this conversation.
    if current_user.id not in (conversation.guest_id, conversation.host_id):
        abort(403)
 
    messages = Message.query.filter_by(conversation_id=id
                                      ).order_by(Message.created_at
                                                ).all()
 
    return jsonify([
        {
            "sender_id": msg.sender_id,
            "user": User.query.get(msg.sender_id).username,
            "body": msg.body,
            "created_at": format_message_time(msg.created_at)
        }
        for msg in messages
    ])

@socketio.on("connect")
def handle_connect():
     if current_user.is_authenticated:
        user_room = f"user_{current_user.id}"
        join_room(user_room)
        
# Mark messages as read
# @socketio.on("read_messages")
# def mark_read(data):
#     conversation_id = data["conversation_id"]
#     Message.query.filter(
#                         Message.conversation_id == conversation_id,
#                         Message.sender_id != current_user.id,
#                         Message.is_read == False ).update({"is_read":True})
#     db.session.commit()
#     emit( "notification_clear", {}, room=f"user_{current_user.id}")

# Mark messages as read
@socketio.on("read_messages")
def mark_read(data):
    if not current_user.is_authenticated:
        return
 
    conversation_id = data.get("conversation_id")
    conversation = Conversation.query.get(conversation_id)
 
    if not conversation:
        return
 
    if current_user.id not in (conversation.guest_id, conversation.host_id):
        return
 
    Message.query.filter(
                        Message.conversation_id == conversation_id,
                        Message.sender_id != current_user.id,
                        Message.is_read == False ).update({"is_read":True})
    db.session.commit()
    emit( "notification_clear", {}, room=f"user_{current_user.id}")

# Add initial count when user loads the page
@udash.route("/chat/unread-count")
@login_required
def unread_count():
    count = Message.query.filter(
            Message.receiver_id == current_user.id,
            Message.is_read == False).count()

    return jsonify({"count": count})

#==================================
@udash.route("/chat/unread-messages")
@login_required
def unread_messages():
    messages = Message.query.filter(
                Message.receiver_id == current_user.id,
                Message.is_read == False
            ).order_by(Message.created_at.desc()
                       ).limit(2).all()

    unread = []

    for msg in messages:
        sender = User.query.get(msg.sender_id)
        unread.append({
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "sender_id": msg.sender_id,
            "sender": sender.username,
            "body": msg.body,
            "time": format_message_time(msg.created_at)
        })

    return jsonify(unread)