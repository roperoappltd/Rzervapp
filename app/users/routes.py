from flask import Blueprint, render_template, flash, redirect, url_for, current_app


users = Blueprint('users', __name__)

@users.route("/login") 
def login():
    '''This function create a route to render the Login page'''
    
    return render_template('pages/login.html',  title='Log in')

@users.route("/signup") 
def signup():
    '''This function create a route to render the Sign up page'''
    
    return render_template('pages/signup.html',  title='Sign up')

@users.route("/uaccount") 
def uaccount():
    '''This function create a route to render user account page''' 
    
    return render_template('users/useraccount.html',  title='Account')

@users.route("/myprofile") 
def myprofile():
    '''This function create a route to render user profile page''' 
    
    return render_template('users/userprofile.html',  title='User Profile')

@users.route("/bookings") 
def bookings():
    '''This function create a route to render user bookings page''' 
    
    return render_template('users/bookings.html',  title='Bookings')

@users.route("/listings") 
def listings():
    '''This function create a route to render user listings page''' 
    
    return render_template('users/listings.html',  title='Bookings')