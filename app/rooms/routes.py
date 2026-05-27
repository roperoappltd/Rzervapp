from flask import (Blueprint, render_template, flash, abort, redirect, request, jsonify,
                   session, url_for, current_app)
from flask_login import current_user, login_required
from app import db
from wtforms.validators import ValidationError
from app.models.usermodel import User
from app.models.roommodel import Rooms, Roomextra, Roomreviews
from app.models.bookmodel import Bookings, Vouchers, Payments, HostEarning, Refund, VoucherUsage
from app.rooms.forms import (UpdateRoomForm, UpdateRoomPictureForm, PaymentForm, RoomSearchForm,
                            RoomExtraForm, RoomReviewsForm, BookingForm, VouchersForm,
                            CancelBookingForm)
from .roomutils import (save_picture, get_total, days_between, current_date, 
                        number_generator, sanitize_input, can_cancel, fee_calculator)
from .notification.bookmail import booking_confirm_email
from .notification.bookcancel import book_cancellation_email
from sqlalchemy import func
from datetime import datetime
import sys
#from app import db

# Creating an instance of the blueprint class
rooms = Blueprint('rooms', __name__)

@rooms.route("/room") 
def room():
    '''This function create a route to render the rooms page'''
    #room = Rooms.query.get_or_404(room_id)
    #dt = booker.created_at
    #deadlines = deadline(dt.date(), 2)
    form = RoomSearchForm()
    # Set a specific page to start with 
    page = request.args.get('page', 1, type=int)
    # Query db to display specific number of room per page (Pagination)

    allrooms = Rooms.query.order_by(Rooms.updated_at.desc()).paginate(
        page=page,
        per_page=6,
        error_out=False
    )

    # Search rooms with expired booking 
    expired_bookings = Bookings.query.filter(
        Bookings.departure < datetime.now(),
        Bookings.active == 'True' or
        Bookings.status == 'Cancelled'
    ).all()

    # Iterate over the list of bookings
    for booking in expired_bookings:
        # LOCK ROOM ROW
        room = Rooms.query.with_for_update().filter_by(
            id=booking.room_id
        ).first()

        if room:
            # Update room status
            room.status = 'Available'
            # Mark booking inactive
            booking.active = 'False'
    # Save the changes in db
    db.session.commit()

    return render_template('pages/rooms.html', title='Rooms Pool', allrooms=allrooms, form=form)

@rooms.route("/roomsearch", methods=["GET", "POST"])
def roomsearch():
    form = RoomSearchForm()
    rooms_found = []

    if form.validate_on_submit():
        query = Rooms.query
        if form.room_location.data:
            query = query.filter(Rooms.room_location.ilike(f"%{form.room_location.data}%"))
        
        elif form.room_category.data:
            query = query.filter(Rooms.room_category.ilike(f"%{form.room_category.data}%"))

        elif form.min_price.data is not None:
            query = query.filter(Rooms.price >= form.min_price.data)

        elif form.max_price.data is not None:
            query = query.filter(Rooms.price <= form.max_price.data)
        else:
            flash('No room found, please refine your search!', 'warning')

        rooms_found = query.all()

        return render_template("pages/roomsearched.html", rooms_found=rooms_found, form=form)

    return render_template("pages/rooms.html", form=form)

@rooms.route("/booknow/<int:room_id>", methods=['GET', 'POST'])
@login_required 
def booknow(room_id):
    '''This function create a route to render the booking page'''
    # fetch the room by id if exist or return 404 if doesnt
    room = Rooms.query.get_or_404(room_id)

    # create room reviews form
    form = BookingForm()
    
    overlapping = db.session.query(Bookings).with_for_update().filter(
        Bookings.room_id == room_id,
        Bookings.status == "Confirmed",
        Bookings.departure >= current_date()
    ).first()

    if overlapping:
        #db.session.rollback()
        flash("Sorry, this room is already booked.", "danger")
        return redirect(url_for('rooms.room'))

    if form.validate_on_submit():
        if room.status == "Available":
            bookinfo = Bookings(booking_num=number_generator(), arrival=form.arrival.data, departure=form.departure.data,
                                num_guests=room.max_occupancy, room_type=room.room_category,
                                ad_info=form.ad_info.data, primary_guest=form.primary_guest.data, 
                                pguest_email=form.pguest_email.data, pguest_phone=form.pguest_phone.data, 
                                room_id=room.id, user_id=current_user.id)
            
            db.session.add(bookinfo)
            db.session.commit()
            
            flash('Booking submitted successfully. Proceed to checkout!', 'success')
            #room.status = "Occupied"
            #db.session.commit()
            return redirect(url_for('rooms.checkout', room_id=room.id))
        else:
            flash('This room is not Available', 'warning')
            return redirect(url_for('rooms.room'))
                
    elif request.method == 'GET':
        form.room_type.data = room.room_category
        form.num_guests.data = room.max_occupancy
        #form.primary_guest.data = f'{current_user.first_name} {current_user.last_name}'
        #form.pguest_email.data = room.user.email
        #form.pguest_phone.data = room.user.phone
    
    return render_template('pages/booking.html', title='Booking', form=form, room=room)

@rooms.route("/cancel-booking/<int:booking_id>", methods=['POST', 'GET'])
@login_required 
def cancel_booking(booking_id):
    booking = Bookings.query.get_or_404(booking_id)
    payment = Payments.query.filter_by(booking_id=booking.id).first()

    # Security check
    if booking.user_id != current_user.id:
        abort(403)

    # Prevent double cancellation
    if booking.status == "Cancelled":
        flash("Booking already cancelled.", "warning")
        return redirect(url_for('rooms.bookings'))
    
    # Cancel booking
    booking.status = "Cancelled"
    booking.active = "False"
    payment.status = "Refundable"

    amount_refundable = payment.total_paid + payment.transac_fee + payment.discount
    refund = Refund(booking_id=booking.id, payment_id=payment.id,
                    user_id=booking.current_user.id, amount=amount_refundable, 
                    status='Pending')
    db.session.add(refund)
    db.session.commit()
    # send msg to user 
    if booking:
        room_id = booking.room_id
        book_cancellation_email(booking, room_id)
        flash(f'Link to view cancellation summary sent to {booking.pguest_email}', 'success')
    else:
        flash('Server error, summary not sent, contact us now', 'warning' )
    
    return redirect(url_for('rooms.bookings'))

@rooms.route("/checkout/<int:room_id>", methods=['GET', 'POST']) 
@login_required
def checkout(room_id):
    '''This function create a route to handle checkout''' 
    room = Rooms.query.get_or_404(room_id)
    book = db.session.query(Bookings).with_for_update().filter(
        Bookings.room_id == room.id,
        Bookings.status == "Pending",
        ).first()

    if not book:
        flash('Server error or booking already created.', 'warning')
        return redirect(url_for('rooms.room'))
    
    #compute bookdays
    bookdays = ( book.departure - book.arrival).days 

    if bookdays <= 0:
        flash("Invalid booking dates.", "warning")
        return redirect(url_for('rooms.roomdetail', room_id=room.id))

    # Import the voucher form
    payform = PaymentForm()
    subtotal = room.price * bookdays 
    total_paid = subtotal
    # default values
    voucher = None
    discount = 0

    # get voucher from session (if any)
    voucher_id = session.get("voucher_id")

    if voucher_id:
        voucher = Vouchers.query.get(voucher_id)
        
        # safety check (must still be valid)
        if voucher:
            existing_usage = VoucherUsage.query.filter_by(voucher_id=voucher.id,
                                            user_id=current_user.id).first()
            if not existing_usage:
                discount = voucher.value
        else:
            session.pop("voucher_id", None)
            voucher = None
    total_paid = max(subtotal - discount, 0)
    # --------------------------------
    # FORM PAYMENT
    # --------------------------------    
    if payform.validate_on_submit():
        t_fees = fee_calculator(total_paid)
        # Create payment record
        payment = Payments(pay_method=payform.pay_method.data, price_per_night=room.price, book_days=bookdays, 
                            discount=discount, status='Paid', total_paid=total_paid - t_fees, 
                            transac_fee=t_fees, user_id=current_user.id, booking_id=book.id, 
                            voucher_id=voucher.id if voucher else None)
        db.session.add(payment)
        db.session.flush()
        # Create hostearning record
        earning = HostEarning(user_id=book.rooms.user_id, booking_id=book.id,
                              payment_id=payment.id, gross_amount=subtotal,
                              voucher_amount=discount, platform_fee=t_fees,
                              net_earning=total_paid)
        db.session.add(earning)
        # Update booking & room status
        book.status = 'Confirmed'
        book.active = 'True'
        room.status = 'Occupied'
        db.session.commit() 
        # Create voucher usage record
        if voucher:
            db.session.flush()
            usage = VoucherUsage(voucher_id=voucher.id, user_id=current_user.id,
                             payment_id=payment.id)
            db.session.add(usage)
            db.session.commit()
        
        return redirect(url_for('rooms.paysuccess', booking_id=book.id))
    # Pass text to submit button    
    #payform.submit.label.text = f"Pay £{total_paid}"
    return render_template('pages/payment.html',  title='Checkout', 
                          room=room, room_id=room.id, book=book, discount=discount,
                          subtotal=subtotal, total_paid=total_paid, payform=payform,
                          voucher_id=voucher_id)

@rooms.route("/check-voucher", methods=["POST"])
#@login_required
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

    # valid
    session["voucher_id"] = voucher.id
    session.modified = True

    # IMPORTANT DEBUG LINE (add this temporarily)
    #print("SESSION SET:", session.get("voucher_id"))

    return jsonify({"message": "<span style='color:green'>valid code, voucher applied</span>",
                    "discount": float(voucher.value)
                    })

@rooms.route("/paysuccess/<int:booking_id>", methods=['GET', 'POST']) 
@login_required
def paysuccess(booking_id):
    '''This function create a route to render payment confirmation page''' 
    # query the db about specific user reviews
    #room = Rooms.query.get_or_404(room_id)
    booking = (
                Bookings.query
                .filter_by(id=booking_id)
                .first_or_404()
            )
    # payment = Payments.query.get_or_404(current_user.id)
    if booking:
        booking_confirm_email(booking, booking.id)
        flash(f'Link to view booking summary sent to {booking.pguest_email}', 'success')
    else:
        flash('Server error, summary not sent, contact us now', 'warning' )
  

    return render_template('pages/paysuccess.html',  title='Pay Success', 
                          booking=booking)

@rooms.route("/roomdetail/<int:room_id>", methods=['GET', 'POST']) 
def roomdetail(room_id):
    '''This function create a route to render the room details page'''
    # fetch the room ads by id if exist or return 404 if doesnt
    room = Rooms.query.get_or_404(room_id)
    # Query someinfo from the db
    roominfo = Rooms.query.filter_by(id=room_id).first()
    roomextra = Roomextra.query.filter_by(id=room_id).first()
    # Room reviews
    reviews = Roomreviews.query.filter_by(room_id=room.id).all()
    totalrev = Roomreviews.query.filter_by(room_id=room.id).count()
    # get the total stars
    ratetot = db.session.query(func.sum(Roomreviews.rate_us).label('tot')).filter_by(room_id=room.id).all()
    # get review score
    revscore = get_total(ratetot, totalrev)
   
    # create room reviews form
    form = RoomReviewsForm()
   
    if form.validate_on_submit():
        clean_msg = sanitize_input(form.message.data)

        if current_user.is_authenticated:
            review = Roomreviews(rate_us=form.rate_us.data , message=clean_msg, room_id=room.id, 
                                user_id=current_user.id)
            db.session.add(review)
            db.session.commit()
            
            flash('Your review has been submitted successfully!', 'success')
            return redirect(url_for('rooms.roomdetail', room_id=room.id))
        else: 
            flash('Please, login or register to review this room!', 'danger')
            return redirect(url_for('users.login'))

    return render_template('pages/roomdetails.html', title='Room Details', 
                           roominfo=roominfo, roomextra=roomextra, form=form,
                           totalrev=totalrev, reviews=reviews, revscore=revscore) #

@rooms.route("/roomextra/<int:room_id>", methods=['GET', 'POST']) 
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
                        concierge=form.concierge.data, room_id=room.id)

        db.session.add(room_extra)                                          # adding data to the database
        db.session.commit()                                                 # saving the changes                                                               
        flash(f"Your room extra has been added successfully.", 'success')   # display validation message 

        return redirect(url_for('users.listings', room_id=room.id))
    
    return render_template('pages/roomextra.html',  title='Room Extra', form=form)

# To update existing room
@rooms.route("/room/update/<int:room_id>", methods=['GET', 'POST'])
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

        # Save changes
        db.session.commit()
        flash('Room details has been successfully updated!', 'success')
        return redirect(url_for('users.listings', room_id=room.id))

    elif request.method == 'GET':
        # Populate the post with the content and tilte of post to update 
        form.room_name.data = room.room_name
        form.room_category.data = room.room_category
        form.short_desc.data = room.short_desc
        form.max_occupancy.data = room.max_occupancy
        form.price.data = room.price
        form.description.data = room.description
        form.status.data = room.status
        form.usp1.data = room.usp1
        form.usp2.data = room.usp2
        form.usp3.data = room.usp3

        #####

    return render_template('pages/listupdate.html',  title='Listing Update', form=form)

# To update existing room
@rooms.route("/update_roompics/<int:room_id>", methods=['GET', 'POST'])
@login_required
def update_roompics(room_id):
    '''This function a create a route to update room images'''
    DEFAULT_IMAGE = 'roomdef1.jpg'
    # fetch the post by id if exist or return 404 if doesnt 
    room = Rooms.query.get_or_404(room_id)
    # Check if the user is the author of the post first 
    if room.user_id != current_user.id:
        abort(403)
    # Create an instance of room form
    form = UpdateRoomPictureForm()
    # adding the logic to validate changes and add to db
    if form.validate_on_submit(): 
        files = form.pictures.data
        # remove empty uploads
        files = [file for file in files if file.filename != '']

        if len(files) > 6:
            flash('Maximum 6 images allowed.', 'danger')
            redirect(url_for('users.listings', room_id=room.id))
        
        image_fields = [
            'image1',
            'image2',
            'image3',
            'image4',
            'image5',
            'image6'
        ]
        
        # First set ALL images to default
        for field in image_fields:
            setattr(room, field, DEFAULT_IMAGE)
        
        # Replace defaults with uploaded images
        for index, file in enumerate(files):
            filename = save_picture(file)
            setattr(
                room,
                image_fields[index],
                filename
            )
        # Save changes
        db.session.commit()

        flash('Room images successfully updated!', 'success')
        return redirect(url_for('users.listings', room_id=room.id))
    
    return render_template('pages/roompicsupdate.html',  title='Picture Update', 
                            form=form)

# route to delete a specific listing
@rooms.route("/room/<int:room_id>/delete", methods=['GET', 'POST'])
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
    flash('Your listing has been successfully deleted!', 'success')
    return redirect(url_for('users.listings', room_id=room.id))
#=====================================================================
@rooms.route("/bookings", methods=['GET', 'POST']) 
@login_required
def bookings():
    '''This function create a route to render user bookings page''' 
    guest_page = request.args.get('guest_page', 1, type=int)
    host_page = request.args.get('host_page', 1, type=int)

    bookguest = db.session.query(Bookings).filter(
                        Bookings.user_id==current_user.id
                        ).order_by(Bookings.created_at.desc()
                                   ).paginate(page=guest_page, 
                                              per_page=3, 
                                              error_out=False)
    
    #booker = db.session.query(Bookings).filter(Bookings.user_id==current_user.id).first()
    bookhost = Bookings.query.join(Rooms).filter(
                        Rooms.user_id==current_user.id
                        ).order_by(Bookings.created_at.desc()
                        ).paginate(page=host_page, 
                                   per_page=3, 
                                   error_out=False)
    
    today = current_date()

    return render_template('userdash/bookings.html',  title='My Bookings', bookguest=bookguest,
                            bookhost=bookhost, today=today, can_cancel=can_cancel)

@rooms.route("/piggybank") 
@login_required
def piggybank():
    '''This function create a route to render user payment page''' 
    page = request.args.get('page', 1, type=int)
    host_earning = HostEarning.query.filter_by(
                                            user_id=current_user.id
                                            ).order_by(HostEarning.created_at.desc()
                                            ).paginate(page=page, 
                                              per_page=4, 
                                              error_out=False)
    
    #allpayments = Payments.query.join(Bookings).join(Rooms).filter(Rooms.user_id == current_user.id).all()
    

    return render_template('userdash/earnings.html',  title='My Earnings', 
                          host_earning=host_earning )

@rooms.route("/refund") 
@login_required
def refund():
    '''This function create a route to render user payment page''' 
    page = request.args.get('page', 1, type=int)
    user_refund = Refund.query.filter_by(user_id=current_user.id
                                        ).order_by(Refund.created_at.desc()
                                        ).paginate(page=page, 
                                            per_page=3, 
                                            error_out=False)
    
    return render_template('userdash/refund.html',  title='My Refund', 
                          user_refund=user_refund )

