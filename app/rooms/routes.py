from flask import Blueprint, render_template, flash, redirect, url_for, current_app
#from app import db

# Creating an instance of the blueprint class
rooms = Blueprint('rooms', __name__)


@rooms.route("/room") 
def room():
    '''This function create a route to render the rooms page'''
    
    return render_template('pages/rooms.html', title='Rooms List')

@rooms.route("/stepsform") 
def stepsform():
    '''This function create a route to render steps form page'''
    
    return render_template('pages/stepsform.html', title='Steps Form')

@rooms.route("/booknow") 
def booknow():
    '''This function create a route to render the booking page'''
    
    return render_template('pages/booking.html', title='Booking')

@rooms.route("/roomdetail") 
def roomdetail():
    '''This function create a route to render the booking page'''
    
    return render_template('pages/roomdetails.html', title='Room Details')

