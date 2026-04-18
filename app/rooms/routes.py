from flask import Blueprint, render_template, flash, abort, redirect, request, url_for, current_app
from flask_login import current_user, login_required
from app import db
from wtforms.validators import ValidationError
from app.models.usermodel import User
from app.models.roommodel import Rooms, Roomextra, Roomreviews
from app.models.bookmodel import Bookings, Vouchers, Payments
from app.rooms.forms import (UpdateRoomForm, UpdateRoomPictureForm, PaymentForm,
                            RoomExtraForm, RoomReviewsForm, BookingForm, VouchersForm)
from .roomutils import save_picture, get_total, days_between
from sqlalchemy import func
import sys
#from app import db

# Creating an instance of the blueprint class
rooms = Blueprint('rooms', __name__)


@rooms.route("/room") 
def room():
    '''This function create a route to render the rooms page'''
    #room = Rooms.query.get_or_404(room_id)
    #totalrev = Roomreviews.query.filter_by(room_id=room.id).count()
    # Set a specific page to start with 
    page = request.args.get('page', 1, type=int)
    # Query db to display specific number of post per page on the home page (Pagination)
    #allrooms = Rooms.query.order_by(Rooms.updated_at.desc()).paginate(page=page, per_page=3)
    allrooms = Rooms.query.order_by(Rooms.updated_at.desc())

    return render_template('pages/rooms.html', title='Our Rooms', allrooms=allrooms)

@rooms.route("/booknow/<int:room_id>", methods=['GET', 'POST'])
@login_required 
def booknow(room_id):
    '''This function create a route to render the booking page'''
    # fetch the room by id if exist or return 404 if doesnt
    room = Rooms.query.get_or_404(room_id)

    # create room reviews form
    form = BookingForm()

    
    if form.validate_on_submit():
            #if current_user.is_authenticated:
        if room.status == "Available":
            bookinfo = Bookings(arrival=form.arrival.data, departure=form.departure.data,
                                num_guests=room.max_occupancy, room_type=room.room_category,
                                ad_info=form.ad_info.data, primary_guest=form.primary_guest.data, 
                                pguest_email=form.pguest_email.data, pguest_phone=form.pguest_phone.data, 
                                room_id=room.id, user_id=current_user.id)
            
            db.session.add(bookinfo)
            db.session.commit()
            
            flash('Booking submitted successfully. You\'ll receive a confirmation mail shortly!', 'success')
            room.status = "Occupied"
            db.session.commit()
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

@rooms.route("/checkout/<int:room_id>", methods=['GET', 'POST']) 
@login_required
def checkout(room_id):
    '''This function create a route to render the booking summary page'''
    # fetch the room by id if exist or return 404 if doesnt
    room = Rooms.query.get_or_404(room_id)
    book = Bookings.query.filter_by(room_id=room.id).first()
    bookdays = days_between(book.departure, book.arrival)
    
    form = PaymentForm()
    form2 = VouchersForm()
    voucher = Vouchers.query.filter_by(code=f'{form2.code.data}').first()
    
    
    # if form2.validate_on_submit():
    #     voucher.value = voucher.value
    #     if voucher.code == form2.code.data:
    #         flash('Great! valid code', 'success')
    #     else:
    #         flash('Bad news! invalid code', 'danger')
    #     return redirect(url_for('rooms.checkout', room_id=room.id))
    
    # if request.method == 'POST':
    #     if form2.validate_on_submit():
    #         voucher.value = voucher.value
            #return redirect(url_for('rooms.checkout'))

    if form2.code.data:
        if form2.validate_on_submit(): 
            reduction = voucher.value

        if form.validate_on_submit():
            if voucher: 
                vouchval = Vouchers.query.filter_by(id=voucher.id).first()
                payment = Payments(pay_method=form.pay_method.data, price_per_night=room.price,
                                book_days=int(bookdays), discount=vouchval.value, 
                                total_paid=(room.price * int(bookdays)) - vouchval.value,
                                user_id=current_user.id, booking_id=book.id, voucher_id=vouchval.id)
                db.session.add(payment)
                db.session.commit() 
                    
                #flash('Your payment has been processed successfully!', 'success')
                return redirect(url_for('rooms.paysuccess'))
            
    return render_template('pages/checkout.html', title='Booking Summary', form=form,
                           form2=form2, book=book, room=room, room_id=room.id,
                           voucher=voucher)

@rooms.route("/paysuccess") 
@login_required
def paysuccess():
    '''This function create a route to render voucher''' 
    # query the db about specific user reviews

    return render_template('pages/paysuccess.html',  title='Pay Success')

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
        if current_user.is_authenticated:
            review = Roomreviews(rate_us=form.rate_us.data , message=form.message.data, room_id=room.id, 
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
        room.usp1 = form.usp1.data
        room.usp2 = form.usp2.data
        room.usp3 = form.usp3.data

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
    '''This function a create a route to update a post'''
    # fetch the post by id if exist or return 404 if doesnt 
    room = Rooms.query.get_or_404(room_id)
    # Check if the user is the author of the post first 
    if room.user_id != current_user.id:
        abort(403)
    # Create an instance of room form
    form = UpdateRoomPictureForm()
    # adding the logic to validate changes and add to db
    if form.validate_on_submit(): 
        if form.picture1.data:  
            picture_file1 = save_picture(form.picture1.data)   
            room.image1 = picture_file1
        if form.picture2.data:  
            picture_file2 = save_picture(form.picture2.data)
            room.image2 = picture_file2
        if form.picture3.data:  
            picture_file3 = save_picture(form.picture3.data) 
            room.image3 = picture_file3 
        if form.picture4.data:  
            picture_file4 = save_picture(form.picture4.data) 
            room.image4 = picture_file4
        if form.picture5.data:  
            picture_file5 = save_picture(form.picture5.data)
            room.image5 = picture_file5
        if form.picture6.data:  
            picture_file6 = save_picture(form.picture6.data)
            room.image6 = picture_file6

        # Save changes
        db.session.commit()
        flash('Room images has been successfully updated!', 'success')
        return redirect(url_for('users.listings', room_id=room.id))

    # elif request.method == 'GET':
    #     # Populate the post with the content and tilte of post to update 
    #     form.picture1.data = room.image1
    #     form.picture2.data = room.image2
    #     form.picture3.data = room.image3
    #     form.picture4.data = room.image4
    #     form.picture5.data = room.image5
    #     form.picture6.data = room.image6
    
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
@rooms.route("/bookings") 
@login_required
def bookings():
    '''This function create a route to render user bookings page''' 
    booklist = db.session.query(Bookings).filter(Bookings.user_id==current_user.id).all()

    return render_template('userdash/bookings.html',  title='My Bookings', 
                            booklist=booklist)