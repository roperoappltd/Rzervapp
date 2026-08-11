from flask import render_template, Blueprint
from flask_login import login_required

administrator = Blueprint('administrator', __name__)



@administrator.route("/stats")
#@login_required
def stats():
    return render_template("adminpanel/bookings.html")




# view endpoint url on flask shell
# from app import db 
# from app import create_app                          
# app = create_app()
# print(app.url_map)