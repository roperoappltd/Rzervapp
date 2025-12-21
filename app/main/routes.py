# Creating a home route 
from flask import Blueprint, render_template, flash, redirect, url_for, current_app
#from app import db

# Creating an instance of the blueprint class
main = Blueprint('main', __name__)

@main.route("/")                                                     
@main.route("/home") 
def home():
    '''This function create a route to render the home page'''
    
    return render_template('pages/homes.html',  title='Home')

@main.route("/about") 
def about():
    '''This function create a route to render the about page'''
    
    return render_template('pages/aboutus.html', title='About us')

@main.route("/contact") 
def contact():
    '''This function create a route to render the contact page'''
    
    return render_template('pages/getintouch.html', title='Contact')

@main.route("/rooms") 
def rooms():
    '''This function create a route to render the rooms page'''
    
    return render_template('pages/rooms.html', title='Rooms List')

@main.route("/booknow") 
def booknow():
    '''This function create a route to render the booking page'''
    
    return render_template('pages/booking.html', title='Booking')

@main.route("/roomdetail") 
def roomdetail():
    '''This function create a route to render the booking page'''
    
    return render_template('pages/roomdetails.html', title='Room Details')

