# ============================================================
# Standard library
# ============================================================
import mimetypes
from datetime import timedelta

# ============================================================
# Flask & extensions
# ============================================================
from flask import Flask, session, request
from flask_login import current_user, LoginManager
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_admin import Admin
from flask_admin.theme import Bootstrap4Theme
from flask_wtf import CSRFProtect
from flask_babel import Babel, _
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

# ============================================================
# App-local
# ============================================================
from app.config import Config


# ============================================================
# One-off runtime fixes
# ============================================================
# Windows' mimetypes registry often doesn't know .webp -- without this,
# Flask's static file server sends it as application/octet-stream, which
# browsers download instead of displaying inline.
mimetypes.add_type('image/webp', '.webp')


# ============================================================
# Extension instances (created here, initialized in create_app())
# ============================================================
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
bcrypt = Bcrypt()
csrf = CSRFProtect()
babel = Babel()

# TODO (production): tighten this to your real domain before deploying --
# "*" allows any origin to open a WebSocket connection to this server.
socketio = SocketIO(cors_allowed_origins="*")
# socketio = SocketIO(cors_allowed_origins=["https://yourdomain.com"])

login_manager = LoginManager()
login_manager.login_view = 'users.login'   # require login to view the account page
login_manager.login_message_category = 'info'

# Custom master template wraps every Flask-Admin page in the site's own
# sidebar/topbar/footer instead of Flask-Admin's default layout.
admin = Admin(theme=Bootstrap4Theme(base_template='adminpanel/master.html'))


# ============================================================
# SQLite foreign-key enforcement
# ============================================================
# SQLite does not enforce foreign key constraints by default -- without
# this, invalid/orphaned FK references can silently exist in dev, then
# surface as unexpected IntegrityErrors the moment this moves to MySQL
# (which enforces FKs by default). Enabling it now, in dev, means any FK
# problems get caught here instead of surprising you in production. Only
# takes effect for SQLite connections -- harmless no-op on MySQL/Postgres.
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ============================================================
# App factory
# ============================================================
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(Config)  # [config_name]

    app.config['LANGUAGES'] = ['en', 'fr']
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

    def get_locale():
        # 1. Explicit choice from the language switcher
        if 'language' in session and session['language'] in app.config['LANGUAGES']:
            return session['language']
        # 2. Fall back to browser preference
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    with app.app_context():
        # ---------------- Initialize extensions ----------------
        db.init_app(app)
        mail.init_app(app)
        migrate.init_app(app, db)
        bcrypt.init_app(app)
        login_manager.init_app(app)
        csrf.init_app(app)
        socketio.init_app(app)
        babel.init_app(app, locale_selector=get_locale)

        # ---------------- Blueprint imports ----------------
        # NOTE: models referenced by db.create_all() below only get
        # created if they've been imported into the process by this
        # point -- either explicitly, or transitively through whichever
        # of these blueprint modules imports them. Given several models
        # this session (User, Conversation, GuestReviews, RoomView,
        # ReviewHelpful) needed explicit importing here specifically to
        # dodge circular-import errors, it's worth double-checking each
        # new model actually gets registered before create_all() runs,
        # rather than assuming a transitive import covers it.
        from app.users.routes import users
        from app.main.routes import main
        from app.rooms.routes import bedrooms
        from app.udashboard.routes import udash
        from app.errors.handlers import errors
        from app.agents.routes import agent
        from app.adminis.routes import administrator
        from app.adminis.views import MyAdminIndexView

        # ---------------- Services ----------------
        from app.services.currency import format_money, convert_and_format, format_room_price, COUNTRY_CURRENCY
        from app.services.geo_service import detect_country, detect_language
        from app.services.preference_service import VisitorPreferences
        from app.services.image_storage import get_room_image_url

        # ---------------- Flask-Admin ----------------
        admin.init_app(app, index_view=MyAdminIndexView())

        # ---------------- Register blueprints ----------------
        app.register_blueprint(users)
        app.register_blueprint(main)
        app.register_blueprint(bedrooms)
        app.register_blueprint(udash)
        app.register_blueprint(errors)
        app.register_blueprint(agent)
        app.register_blueprint(administrator, url_prefix="/admin")

        # ---------------- Create tables ----------------
        # FIXED: db.create_all() ran here unconditionally, but Gunicorn
        # launches multiple separate WORKER PROCESSES (--workers 3),
        # each independently calling create_app() on startup -- all
        # three race to create the same tables simultaneously. The
        # first worker to reach a given CREATE TABLE succeeds; any
        # other worker reaching the same statement moments later
        # crashes with "table already exists", since MySQL (unlike
        # SQLite locally, where this race never surfaced) doesn't
        # silently no-op on a duplicate CREATE TABLE. Catching
        # specifically MySQL's error code 1050 here -- it means another
        # worker already succeeded, not a real problem -- while letting
        # any other, genuine error still propagate and crash startup as
        # it should.
        try:
            db.create_all()
        except OperationalError as e:
            if not (e.orig and getattr(e.orig, "args", [None])[0] == 1050):
                raise

    # ---------------- Context processors ----------------
    @app.context_processor
    def inject_currency():
        return dict(format_money=format_money, convert_and_format=convert_and_format, format_room_price=format_room_price)

    @app.context_processor
    def inject_image_helpers():
        return dict(get_room_image_url=get_room_image_url)

    @app.context_processor
    def inject_preferences():
        prefs = VisitorPreferences()
        return dict(
            get_locale=get_locale,
            current_language=prefs.language,
            preferred_currency=prefs.currency,
            visitor_country=prefs.country,
        )

    # ---------------- CLI commands ----------------
    @app.cli.command("update-exchange-rates")
    def update_exchange_rates_command():
        '''Fetches current rates and updates ExchangeRate.
        Test locally with: flask update-exchange-rates
        Scheduled later via cron on the VPS -- see the crontab example
        below. Provides its own Flask app context automatically, so it
        can run standalone, outside of a live request.'''
        from app.services.exchange_updater import update_exchange_rates
        
        success, message = update_exchange_rates()
        print(message)

    @app.cli.command("run-booking-maintenance")
    def run_booking_maintenance_command():
        '''Periodic booking housekeeping -- previously split between this
        and running inline on every /rooms page visit, now consolidated
        here. Four independent things, each explicitly recorded via
        status_reason where the status itself is ambiguous about cause:

        1. Pending, abandoned mid-checkout, past the resume window ->
           Expired, reason 'pending_timeout'.
        2. Pending, never paid, and the stay dates have now ALSO passed
           -> Expired, reason 'departure_passed_unpaid'. Explicitly
           excludes anything already handled by #1, rather than relying
           on query-ordering/autoflush timing to avoid double-processing.
        3. Confirmed, stay concluded -> status stays Confirmed on purpose
           (mybookings.html depends on this exact status for the Rate
           Guest/Rate Stay buttons -- changing it would silently break
           that feature). Only status_reason is set, as a marker layered
           on top, skipping rows already marked so repeated runs don't
           re-touch the same bookings.
        4. Already-Cancelled bookings still flagged active=True ->
           active set to False. Status itself untouched (was already
           correct) -- moved here from room(), which ran this on every
           single page visit.

        Test locally with: flask run-booking-maintenance
        Schedule via cron alongside update-exchange-rates.'''
        from datetime import datetime, timedelta
        from app.models.bookmodel import Bookings
        from app.helpers.booking import PENDING_BOOKING_EXPIRY_MINUTES

        now = datetime.utcnow()
        resume_cutoff = now - timedelta(minutes=PENDING_BOOKING_EXPIRY_MINUTES)

        # 1. Abandoned mid-checkout, resume window elapsed
        timed_out = Bookings.query.filter(
            Bookings.status == 'Pending',
            Bookings.created_at < resume_cutoff,
        ).all()
        timed_out_ids = {b.id for b in timed_out}
        for booking in timed_out:
            booking.status = 'Expired'
            booking.status_reason = 'pending_timeout'
            booking.active = False

        # 2. Never paid, stay dates also passed -- explicitly excludes
        # #1's rows rather than relying on implicit query timing
        never_paid_filters = [Bookings.status == 'Pending', Bookings.departure < now]
        if timed_out_ids:
            never_paid_filters.append(~Bookings.id.in_(timed_out_ids))
        never_paid = Bookings.query.filter(*never_paid_filters).all()
        for booking in never_paid:
            booking.status = 'Expired'
            booking.status_reason = 'departure_passed_unpaid'
            booking.active = False

        # 3. Successfully completed stays -- status stays Confirmed,
        # only the reason marker is added. Skips already-marked rows so
        # repeated runs don't keep re-touching the same bookings.
        completed = Bookings.query.filter(
            Bookings.status == 'Confirmed',
            Bookings.departure < now,
            Bookings.status_reason.is_(None),
        ).all()
        for booking in completed:
            booking.status_reason = 'stay_completed'

        # 4. Already-cancelled bookings still flagged active
        still_active_cancelled = Bookings.query.filter(
            Bookings.status == 'Cancelled',
            Bookings.active == True,
        ).all()
        for booking in still_active_cancelled:
            booking.active = False

        db.session.commit()
        print(f"Expired (checkout timeout): {len(timed_out)}")
        print(f"Expired (unpaid, past departure): {len(never_paid)}")
        print(f"Marked stay_completed: {len(completed)}")
        print(f"Deactivated cancelled: {len(still_active_cancelled)}")

    return app