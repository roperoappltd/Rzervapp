from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models.usermodel import User
from .forms import (LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm, UpdateAccountForm)
from .usermails.resetrequest import send_reset_email
from .utils import save_picture

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

@users.route("/reset_password", methods=['GET', 'POST'])             # Creating a reset password request route                                            
def reset_request():
    '''This function enable users to send password reset request'''
    # Making sure that user is redirect to home page 
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    # Creating a request password reset form
    form = RequestResetForm() 
    if form.validate_on_submit():
        # validate if user email enter in form is same email in record
        user = User.query.filter_by(email=form.email.data).first()
        # call funtion that send a reset email to the user 
        send_reset_email(user)
        flash(f'An email has been sent to {user} with instructions to reset your password!', 'info')
        return redirect(url_for('users.login'))
    return render_template('pages/reset_request.html', title='Reset Password', form=form)

@users.route("/reset_password/<token>", methods=['GET', 'POST'])             # Creating a reset password route                                            
def reset_token(token):
    '''This function enable to reset user password'''
    # Making sure that user is redirect to home page 
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    # generating a token & pass it in to the user
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():                                                          # form validation
        hashed_pass = bcrypt.generate_password_hash(form.password.data).decode("utf-8")    # Hashing user password
        user.password = hashed_pass                                                        # setting the user new password
        db.session.commit()                                                                # saving the changes 
        flash("Your Password has been Updated!. You can now Log in. " , 'success')         # display validation message [ f'Account created for {form.username.data}!' ]
        return redirect(url_for('users.login'))
    return render_template('pages/reset_token.html', title='Reset Password', form=form)

@users.route("/uaccount") 
def uaccount():
    '''This function create a route to render user account page''' 
    
    return render_template('userdash/useraccount.html',  title='User Account')

@users.route("/myprofile", methods=['GET', 'POST'])
@login_required 
def myprofile():
    '''This function create a route to render user profile page''' 
    form = UpdateAccountForm()
    
    if form.validate_on_submit():
        if form.picture.data:    # check if profile picture has been uploaded
            picture_file = save_picture(form.picture.data)
            # set the profile image file
            current_user.image_file = picture_file
        # allow update if username & email is valid
        current_user.company_name = form.company_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.gender = form.gender.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.city = form.city.data
        current_user.country = form.country.data
        current_user.zip_code = form.zip_code.data
        current_user.aboutme = form.aboutme.data
       
        # save the db entry
        db.session.commit()
        # Displaying an update message
        flash('Your profile has been successfully updated', 'success')
        # redirect after update to the account page
        return redirect(url_for('users.uaccount'))
    # populate the form field with the user data
    elif request.method == 'GET':
        form.company_name.data =  current_user.company_name 
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.gender.data = current_user.gender
        form.phone.data = current_user.phone
        form.address.data = current_user.address
        form.city.data = current_user.city
        form.country.data = current_user.country
        form.zip_code.data = current_user.zip_code
        form.aboutme.data = current_user.aboutme
            
    
    # set cuurent user profile pictures to pass to the current default image
    image_file = url_for('static', filename='userpics/' + current_user.image_file) 
        
    return render_template('userdash/userprofile.html', title='Account', image_file=image_file, form=form )

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