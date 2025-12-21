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