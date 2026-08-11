from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from flask_babel import _

def email_verified_required(f):
    '''Stack under @login_required on any route that creates a booking or
    a room listing. Assumes @login_required already ran, so current_user
    is guaranteed authenticated by the time this checks email_verified.'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.email_verified:
            flash(_('Please verify your email before booking or listing a room.'), 'warning')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function