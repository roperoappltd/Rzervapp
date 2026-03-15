from flask import Blueprint, render_template, flash, abort, redirect, request, url_for, current_app
from flask_login import current_user, login_required
from app import db
from app.models.usermodel import User
from app.models.roommodel import Rooms, Roomextra
from app.rooms.forms import (UpdateRoomForm, UpdateRoomPictureForm, 
                            RoomExtraForm)
from .roomutils import save_picture
#from app import db

# Creating an instance of the blueprint class
rooms = Blueprint('rooms', __name__)


@rooms.route("/room") 
def room():
    '''This function create a route to render the rooms page'''
    
    return render_template('pages/rooms.html', title='Rooms List')

@rooms.route("/booknow") 
def booknow():
    '''This function create a route to render the booking page'''
    
    return render_template('pages/booking.html', title='Booking')

@rooms.route("/roomdetail") 
def roomdetail():
    '''This function create a route to render the booking page'''
    roominfo = Rooms.query.filter_by(id=5).first()
    
    return render_template('pages/roomdetails.html', title='Room Details', 
                           roominfo=roominfo)

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
                        tv=form.tv.data, kitchen=form.kitchen.data, towels=form.towels.data,
                        resto=form.resto.data, bar=form.bar.data, spa=form.spa.data, 
                        shop=form.shop.data, concierge=form.concierge.data, room_id=room.id)

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
        room.image1 = save_picture(form.picture1.data)
        room.image2 = save_picture(form.picture2.data)
        room.image3 = save_picture(form.picture3.data)

        # Save changes
        db.session.commit()
        flash('Room images has been successfully updated!', 'success')
        return redirect(url_for('users.listings', room_id=room.id))

    # elif request.method == 'GET':
    #     # Populate the post with the content and tilte of post to update 
    #     form.picture1.data = room.image1
    #     form.picture2.data = room.image2
    #     form.picture3.data = room.image3
    
    return render_template('pages/roompicsupdate.html',  title='Listing Update', 
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
#===============================================