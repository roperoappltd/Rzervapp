# Creating a home route 
from flask import Blueprint, render_template, flash, redirect, url_for, current_app
#from app import db

# Creating an instance of the blueprint class
main = Blueprint('main', __name__)

@main.route("/")                                                     
@main.route("/home") 
def home():
    '''This function create a route to render the home page'''
    
    return render_template('pages/homes.html')
