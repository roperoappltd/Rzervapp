from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models.usermodel import User
from app.models.roommodel import Rooms, Roomreviews
from app.models.bookmodel import Bookings, HostEarning, Withdrawal
from .forms import (LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm,
                    DeleteAccountForm)
from app.rooms.forms import AddRoomForm, UpdateRoomForm
from app.rooms.roomutils import can_cancel
from app.helpers.cancel_checks import cancel_and_refund_if_paid
from app.services.preference_service import VisitorPreferences
from .usermails.resetrequest import send_reset_email
from .usermails.joinusmail import member_regismail
from .utils import save_picture
from ..rooms.roomutils import sanitize_input
from flask_babel import _
from datetime import datetime, timedelta
from app.helpers.login_security import (is_safe_redirect_url, MAX_FAILED_ATTEMPTS, 
                                        LOCKOUT_DURATION_MINUTES)
import cv2
from datetime import date, timedelta

users = Blueprint('users', __name__)


@users.route("/login" , methods=['GET', 'POST']) 
def login():
    '''This function enable users to login to their account'''
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
 
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
 
        # Treat a soft-deleted account exactly like a non-existent one --
        # same generic message, same dummy-cost bcrypt check below. If we
        # gave a distinct "this account was deleted" message, that would
        # leak which emails used to be real accounts, reopening the exact
        # enumeration gap the timing-safe check further down exists to close.
        if user and user.deleted_at is not None:
            user = None
 
        # If a previous lockout window has passed, clear it and give a
        # fresh set of attempts rather than instantly re-locking on the
        # next single failure.
        if user and user.locked_until and user.locked_until <= datetime.utcnow():
            user.locked_until = None
            user.failed_login_attempts = 0
            db.session.commit()
 
        # Check lockout BEFORE attempting any password verification.
        # Deliberately reusing the exact same generic message as invalid
        # credentials below -- a distinct "too many attempts" message would
        # confirm to an attacker that this account exists AND is currently
        # locked, which is real information disclosure.
        if user and user.locked_until and user.locked_until > datetime.utcnow():
            flash(_('Login unsuccessful, Please check email and password!'), 'danger')
            return render_template('pages/login.html', title='Log in', form=form)
 
        # Always run a bcrypt check, even when no user exists, so the
        # response takes the same amount of time either way -- otherwise
        # a fast response (no bcrypt call at all) leaks that the email
        # doesn't exist, and a slow one leaks that it does.
        if user:
            password_valid = bcrypt.check_password_hash(user.password, form.password.data)
        else:
            bcrypt.check_password_hash('$2b$12$' + 'x' * 53, form.password.data)  # dummy-cost check, result discarded
            password_valid = False
 
        if user and password_valid:
            # Successful login -- clear any accumulated failed attempts.
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            db.session.commit()
 
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
 
            if next_page and is_safe_redirect_url(next_page):
                return redirect(next_page)
            return redirect(url_for('main.home'))
        else:
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                db.session.commit()
 
            flash(_('Login unsuccessful, Please check email and password!'), 'danger')
    
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
                    password=hashed_pass,
                    terms_accepted=form.terms.data,
                    terms_accepted_at=datetime.utcnow(),
                    language=VisitorPreferences().language)  # NEW: was never set, always sat at the 'en' 
                                                             # default regardless of the visitor's actual detected language

        db.session.add(user)                                                               
        db.session.commit()  
        # send account verification email to user
        member_regismail(user)
        # Flash confirmation msg
        flash(_('Account created! Please check your email to verify your account.'), 'info')  # saving the changes 

        return redirect(url_for('users.login'))

    return render_template('pages/register.html', title='Sign up', form=form)

# Creating a logout route 
@users.route("/logout")                           
def logout():
    '''This function enable users to logout from their account'''
    logout_user()
    flash(_('You are now logged out of the system'), 'success' )
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
        # get current user email
       
        flash(_(f'An email has been sent to {user.email} with instructions to reset your password!'), 'info')
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
        flash(_('That is an invalid or expired token'), 'warning')
        return redirect(url_for('users.reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():                                                          # form validation
        hashed_pass = bcrypt.generate_password_hash(form.password.data).decode("utf-8")    # Hashing user password
        user.password = hashed_pass                                                        # setting the user new password
        db.session.commit()                                                                # saving the changes 
        flash(_("Your Password has been Updated!. You can now Log in.") , 'success')         # display validation message [ f'Account created for {form.username.data}!' ]
        return redirect(url_for('users.login'))
    return render_template('pages/reset_token.html', title='Reset Password', form=form)


# Add this inside your existing registration/signup route, right after
# the new User row is committed to the database:

    verify_url = url_for('users.verify_email', token=user.get_verification_token(), _external=True)
    msg = Message('Verify your Jambo account', recipients=[user.email])
    msg.body = f"Welcome to Jambo! Please verify your email by visiting: {verify_url}"
    # or msg.html = render_template('email/verify_email.html', verify_url=verify_url)
    mail.send(msg)

    flash(_('Account created! Please check your email to verify your account.'), 'info')


# New route -- add this alongside your other users.routes:

@users.route("/verify-email/<token>")
def verify_email(token):
    user = User.verify_verification_token(token)

    if user is None:
        flash(_('That verification link is invalid or has expired.'), 'danger')
        return redirect(url_for('main.home'))

    if user.email_verified:
        flash(_('Your email is already verified.'), 'info')
        return redirect(url_for('users.login'))

    user.email_verified = True
    user.email_verified_at = datetime.utcnow()
    db.session.commit()

    flash(_('Your email has been verified! You can now log in.'), 'success')
    return redirect(url_for('users.login'))

@users.route("/delete-account", methods=['GET', 'POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()

    # --------------------------------------------------------------
    # HOST-SIDE CHECK: does this user have any upcoming guests booked
    # into rooms they host? Unconditional block -- unlike a guest
    # cancelling their own trip, a host disappearing on a guest who's
    # already paid and expecting a stay is a much bigger trust problem
    # than a delayed refund. No auto-resolution offered; the host must
    # deal with these bookings first (contact guests, let stays
    # complete, or go through normal cancellation) before they can delete.
    # --------------------------------------------------------------
    hosted_upcoming = (
        Bookings.query.join(Rooms, Bookings.room_id == Rooms.id)
        .filter(
            Rooms.user_id == current_user.id,
            Bookings.status == 'Confirmed',
            Bookings.departure > date.today(),
        )
        .count()
    )
    if hosted_upcoming > 0:
        flash(_("You have upcoming guests booked into your rooms. Please resolve these bookings before deleting your account."), "danger")
        return redirect(url_for('udash.udashboard'))  # adjust to your actual dashboard route name

    # --------------------------------------------------------------
    # GUEST-SIDE CHECK: does this user have a Confirmed trip of their
    # own that's past the point where can_cancel() would allow a full
    # refund? Block rather than silently cancel with no refund -- the
    # platform shouldn't keep money for a trip it unilaterally cancelled.
    # --------------------------------------------------------------
    own_confirmed = Bookings.query.filter(
        Bookings.user_id == current_user.id,
        Bookings.status == 'Confirmed',
        Bookings.departure > date.today(),
    ).all()

    non_cancellable = [b for b in own_confirmed if not can_cancel(b.status, b.arrival)]
    if non_cancellable:
        flash(_("You have an upcoming trip that can no longer be freely cancelled. Please contact us before deleting your account."), "danger")
        return redirect(url_for('udash.mybookings'))  # adjust to your actual bookings route name

    if form.validate_on_submit():
        if not bcrypt.check_password_hash(current_user.password, form.password.data):
            flash(_('Incorrect password. Account not deleted.'), 'danger')
            return render_template('pages/delete_account.html', title='Delete Account', form=form)

        # Everything below happens in one transaction.

        # Auto-cancel the user's own remaining eligible bookings (Pending,
        # or Confirmed-and-still-within-the-cancellation-window -- we
        # already proved above that nothing past that window exists).
        for booking in Bookings.query.filter(
            Bookings.user_id == current_user.id,
            Bookings.status.in_(['Pending', 'Confirmed']),
            Bookings.departure > date.today(),
        ).all():
            cancel_and_refund_if_paid(booking, reason='account_deleted')

        # Hide every room this user hosts -- safe to do now, we already
        # confirmed above there are no upcoming guests booked into them.
        for room in Rooms.query.filter_by(user_id=current_user.id).all():
            room.status = 'Hidden'

        current_user.soft_delete()
        db.session.commit()

        logout_user()
        flash(_('Your account has been deleted.'), 'info')
        return redirect(url_for('main.home'))

    return render_template('pages/delete_account.html', title='Delete Account', form=form)

# =======================================================================================
@users.route("/capture_image") 
def capture_image(camera_index=0):
    ''' 
        Capture an image from the specified webcam on click
        args: 
            camera_index: Index of the webcam to use (default: 0)
    '''
    # Initialize video capture object 
    cap = cv2.VideoCapture(camera_index)

    # check if camera opened succesfully 
    if not cap.isOpened():
        print("Failed to open camera")
        return
    
    # Create a window to display the webcam feed
    cv2.namedWindow("Webcam Feed", cv2.WINDOW_NORMAL)

    # Track the click event 
    clicked = False
    def click_event(event, x, y, flags, param):
        nonlocal clicked
        # set clicked flag to True only on left mouse button event 
        if event == cv2.EVENT_LBUTTONDOWN:
            clicked = True
    #set mouse click callback function 
    cv2.setMouseCallback("Webcam Feed", click_event)
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        #check if the frame is read correctly
        if not ret:
            print("Fail to capture an image")
            break
        # Display the webcam feed
        cv2.imshow("Webcam Feed", frame)
        # Capture image on click 
        if clicked:
            # Get current timestamp for filemane 
            #timestamp = str(int(round(time.time() + 1000)))
            # Save captured image
            #cv2.imwrite(f"webcam_image_{timestamp}.jpg", frame)
            cv2.imwrite(f"app/static/userpics/takeapics/{current_user.username}.jpg", frame)  
            print("Image captured successfully!")
            # Reset clicked flag
            clicked = False
        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # Release capture object
    cap.release()
    cv2.destroyAllWindows()
    return '', 204