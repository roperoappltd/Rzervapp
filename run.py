
from datetime import timedelta
from flask import session, g
from flask_login import current_user
from app import create_app, socketio

# from flask_track_usage import TrackUsage
# from flask_track_usage.storage.sql import SQLStorage

app = create_app()
app.app_context().push

# Implementing a session timeout after 1 minute of inactivity
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)
    session.modified = True
    g.user = current_user

if __name__ == "__main__":
    # The Werkzeug debugger lets anyone who reaches it run code on the
    # machine, so it is OFF inside Docker (the VPS) and when FLASK_DEBUG=0.
    # Locally it stays on as before; FLASK_DEBUG=1/0 overrides either way.
    import os
    _flag = os.getenv("FLASK_DEBUG")
    _debug = (_flag == "1") if _flag is not None else not os.path.exists("/.dockerenv")
    socketio.run(app, debug=_debug, allow_unsafe_werkzeug=True)

# if __name__ == '__main__':
#     app.run(debug=True) 

# pip freeze > requirements.txt