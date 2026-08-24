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
            # AMENDED: previously redirected to home with a generic
            # message and no way to act on it -- this is exactly the
            # moment someone discovers they're blocked, so a dead end
            # here is the worst place for one. Now states the reason
            # and sends them straight to the fix.
            flash(_("Unverified email. Please use the link provided in your email to verify. Alternatively, enter your email to obtain a new verification link."), 'warning')
            return redirect(url_for('users.resend_verification'))
        return f(*args, **kwargs)
    return decorated_function