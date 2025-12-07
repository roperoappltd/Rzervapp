from flask import Blueprint, render_template, session
from app.models import db, User
#from app.csrf import CSRFError


# Creating an instance of blueprint
errors = Blueprint('errors', __name__)

# create error handlers route for error code 404 page not found
@errors.app_errorhandler(404)
def error_404(error):    
    return render_template('errors/404.html'), 404

# error handler for code 403
@errors.app_errorhandler(403)
def error_403(error):
    #user = User()
    #if session.new:
    #    session['anonymous_user_id'] = user.id
    return render_template('errors/403.html'), 403

# error handler for code 500
@errors.app_errorhandler(500)
def error_404(error):
    return render_template('errors/404.html'), 500

# error handler for CSRF 
# @errors.app_errorhandler(CSRFError)
# def error_csrf(e):
#     return render_template('errors/csrf.html'), 400
