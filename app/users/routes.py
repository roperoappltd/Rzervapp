from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models.usermodel import User
from .forms import (LoginForm, RegistrationForm)

users = Blueprint('users', __name__)

@users.route("/login" , methods=['GET', 'POST']) 
def login():
    '''This function enable users to login to their account'''
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            # redirecting to the right page after been force to authenticate
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful, Please check email and password!', 'danger')
    
    return render_template('pages/login.html',  title='Log in', form=form)

@users.route("/signup", methods=['GET', 'POST']) 
def signup():
    '''This function create a route to render the Sign up page
       for users to register to create an account'''
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))  # redirect already authenticated users to the home
    
    form = RegistrationForm()
    if form.validate_on_submit():                                                          # form validation
        hashed_pass = bcrypt.generate_password_hash(form.password.data).decode("utf-8")    # Hashing user password
        user = User(first_name=form.first_name.data, last_name=form.last_name.data,
                    username=form.username.data, dob=form.dob.data, email=form.email.data,
                    password=hashed_pass, terms=form.terms.data)
        db.session.add(user)                                                               # adding the user to the database
        db.session.commit()                                                                # saving the changes                                                               
        flash(f"Your account have been created!. A verification email will be sent to you shortly.", 'success')     # display validation message [ f'Account created for {form.username.data}!' ]
        # send account verification email to user
        #member_registration(user)

        # Sending an activation email to new users
        # activation_email(user)
        return redirect(url_for('users.login'))

    return render_template('pages/register.html', title='Sign up', form=form)

# Creating a logout route 
@users.route("/logout")                           
def logout():
    '''This function enable users to logout from their account'''
    logout_user()
    flash('You are now logged out of the system', 'success' )
    return redirect(url_for('users.login')) 

@users.route("/uaccount") 
def uaccount():
    '''This function create a route to render user account page''' 
    
    return render_template('userdash/useraccount.html',  title='User Account')

@users.route("/myprofile") 
def myprofile():
    '''This function create a route to render user profile page''' 
    
    return render_template('userdash/userprofile.html',  title='Profile')

@users.route("/bookings") 
def bookings():
    '''This function create a route to render user bookings page''' 
    
    return render_template('userdash/bookings.html',  title='Bookings')

@users.route("/listings") 
def listings():
    '''This function create a route to render user listings page''' 
    
    return render_template('userdash/listings.html',  title='Listings')

@users.route("/earnings") 
def earnings():
    '''This function create a route to render user earnings page''' 
    
    return render_template('userdash/earnings.html',  title='Earnings')