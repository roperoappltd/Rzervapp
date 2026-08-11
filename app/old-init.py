from flask import Flask, session, request
from flask_login import current_user
from app.config import Config 
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_admin import Admin
from flask_admin.theme import Bootstrap4Theme
from flask_wtf import CSRFProtect
from datetime import timedelta
from flask_babel import Babel, _
import mimetypes
mimetypes.add_type('image/webp', '.webp')


# Create db object
db = SQLAlchemy()

# SQLite does not enforce foreign key constraints by default -- without
# this, invalid/orphaned FK references can silently exist in dev, then
# surface as unexpected IntegrityErrors the moment this moves to MySQL
# (which enforces FKs by default). Enabling it now, in dev, means any
# FK problems get caught here instead of surprising you in production.
# This only takes effect for SQLite connections -- harmless no-op on
# MySQL/Postgres, which don't understand this PRAGMA and this listener
# only fires for sqlite3 connections anyway.
from sqlalchemy import event
from sqlalchemy.engine import Engine
 
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Create flask migrate object
migrate = Migrate()
# Create flask mail object
mail = Mail() 
# creating a bcrypt instance for password hashing
bcrypt = Bcrypt()
# initializing csrf
csrf = CSRFProtect()
# Initializing socketio
socketio = SocketIO(cors_allowed_origins="*")
# socketio = SocketIO(cors_allowed_origins=["https://yourdomain.com"])
# Initialized babel for multi-language
babel = Babel()

# create an instance of loginManager 
login_manager = LoginManager()
login_manager.login_view = 'users.login'   # exige login to view the account page
login_manager.login_message_category = 'info'

# integrate flask admin
admin = Admin(theme=Bootstrap4Theme(base_template='adminpanel/master.html'))

def create_app(config_name='default'):
    from app import db

    app = Flask(__name__)
    # Load the proper configuration
    app.config.from_object(Config) #[config_name]

    app.config['LANGUAGES'] = ['en', 'fr']
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

    def get_locale():
        # 1. Explicit choice from your language switcher
        if 'language' in session and session['language'] in app.config['LANGUAGES']:
            return session['language']
        # 2. Fall back to browser preference
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    with app.app_context():
        # Initialize extensions
        db.init_app(app)
        mail.init_app(app)
        migrate.init_app(app, db)
        bcrypt.init_app(app)
        login_manager.init_app(app)
        csrf.init_app(app)
        socketio.init_app(app)
        babel.init_app(app, locale_selector=get_locale)

        # Imports our route blueprints
        #from app.enrolls.routes import enrolls
        from app.users.routes import users
        from app.main.routes import main
        from app.rooms.routes import bedrooms
        from app.udashboard.routes import udash
        from app.errors.handlers import errors
        from app.agents.routes import agent 
        #from app.models import Controller_AdminView
        from app.services.currency import format_money, convert_and_format, COUNTRY_CURRENCY
        from app.services.geo_service import detect_country, detect_language
        from app.services.preference_service import VisitorPreferences
        from app.adminis.routes import administrator
        from app.adminis.views import MyAdminIndexView

        #from flask_track_usage import TrackUsage
        #from flask_track_usage.storage.sql import SQLStorage

        # initialize the admin controller view
        #admin.init_app(app, index_view=Controller_AdminView())
        admin.init_app(app, index_view=MyAdminIndexView())

        # Register our blueprints
        #app.register_blueprint(enrolls)
        app.register_blueprint(users)
        app.register_blueprint(main)
        app.register_blueprint(bedrooms)
        app.register_blueprint(udash)
        app.register_blueprint(errors)
        app.register_blueprint(agent)
        app.register_blueprint(administrator , url_prefix="/admin")
       
        # Create database tables
        #db.create_all()
        
    # adding a context processor
    @app.context_processor
    def inject_currency():
        return dict(format_money=format_money, convert_and_format=convert_and_format)

    # @app.context_processor
    # def inject_preferences():
    #     return {"preferred_currency": session.get("currency", "GBP")}
    
    @app.context_processor
    def inject_preferences():

        prefs = VisitorPreferences()

        return dict(get_locale=get_locale,
                    current_language=prefs.language,
                    preferred_currency=prefs.currency,
                    visitor_country=prefs.country
                )  

    @app.cli.command("init-db")
    def init_db():
        """Create tables directly from models — first-time setup only.

        This bypasses Flask-Migrate on purpose: it's for getting a brand-new
        dev database running quickly, not for ongoing schema changes. Once
        you're up and running, use `flask db migrate` / `flask db upgrade`
        for anything after this — mixing the two on the same database will
        confuse Alembic's migration history.
        """
        with app.app_context():
            db.create_all()
        print("Database tables created.")  

            
    return app 
