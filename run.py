
from datetime import timedelta
from flask import session, g
from flask_login import current_user
from app import create_app

# from flask_track_usage import TrackUsage
# from flask_track_usage.storage.sql import SQLStorage

app = create_app()
app.app_context().push

# Implementing a session timeout after 1 minute of inactivity
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)
    session.modified = True
    g.user = current_user

if __name__ == '__main__':
    app.run(debug=True) 
