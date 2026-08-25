from flask import Blueprint, render_template, flash, redirect, request, url_for
from app import db
from flask_wtf.csrf import CSRFError
from flask_babel import _
from sqlalchemy.exc import DataError
import re


# Creating an instance of blueprint
errors = Blueprint('errors', __name__)

# create error handlers route for error code 404 page not found
# error handler for code 403
@errors.app_errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403

@errors.app_errorhandler(404)
def error_404(error):    
    return render_template('errors/404.html'), 404

# error handler for code 500
# FIXED: was rendering errors/404.html -- showed a "page not found"
# message to someone who'd actually hit a real server error, which
# genuinely exists as its own template but was never wired up. Also
# renamed from error_404 (duplicate function name shared with the
# actual 404 handler above -- harmless since Flask registers by status
# code, not function name, but confusing to read).
@errors.app_errorhandler(500)
def error_500(error):
    return render_template('errors/500.html'), 500

# error handler for CSRF 
@errors.app_errorhandler(CSRFError)
def error_csrf(e):
    return render_template('errors/csrf.html'), 400

# Catches "Data too long for column" and similar DB-level length/type
# errors anywhere in the app, rather than requiring every individual
# form or route to guard against this manually. Two things this MUST
# do: roll back the broken session (without this, the session stays
# unusable and the next query on it also fails -- exactly the
# secondary PendingRollbackError this was built to prevent), and show
# something actionable instead of a raw 500.
@errors.app_errorhandler(DataError)
def error_data_too_long(error):
    db.session.rollback()

    # MySQL's own message names the specific column, e.g.
    # "Data too long for column 'room_name' at row 1" -- parsed out
    # when possible so the message can name the actual field, falling
    # back to a generic message if the format doesn't match (e.g. a
    # different DB error entirely, or a driver with different wording).
    match = re.search(r"column '(\w+)'", str(error.orig))
    if match:
        field_name = match.group(1).replace('_', ' ').title()
        message = _("%(field)s is too long. Please shorten it and try again.", field=field_name)
    else:
        message = _("One of the values entered is too long. Please shorten it and try again.")

    flash(message, 'danger')
    return redirect(request.referrer or url_for('main.home'))