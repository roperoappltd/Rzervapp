from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from app.models.roommodel import Rooms
#from app import db

# Creating an instance of the blueprint class
main = Blueprint('main', __name__)

@main.route("/")                                                     
@main.route("/home") 
def home():
    '''This function create a route to render the home page'''
    # fetch a post by id if exist or return 404 if doesnt 
    spotlight = Rooms.query.filter_by(id=2).first()
    spotlight2 = Rooms.query.filter_by(id=5).first()
    spotlight3 = Rooms.query.filter_by(id=1).first()
    #roomids = Rooms.query.all()


    image1 = url_for('static', filename='userpics/roompics/' + spotlight.image1)
    image2 = url_for('static', filename='userpics/roompics/' + spotlight2.image1)
    image3 = url_for('static', filename='userpics/roompics/' + spotlight3.image1)
    return render_template('pages/homes.html',  title='Home', spotlight=spotlight, 
                            spotlight2=spotlight2, spotlight3=spotlight3, image1=image1, 
                            image2=image2, image3=image3)

@main.route("/about") 
def about():
    '''This function create a route to render the about page'''
    
    return render_template('pages/aboutus.html', title='About us')

@main.route("/contact") 
def contact():
    '''This function create a route to render the contact page'''
    
    return render_template('pages/getintouch.html', title='Contact')