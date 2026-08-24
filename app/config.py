import os
from dotenv import load_dotenv

load_dotenv()

#----------------------------------------------------------------------------------
# Create configuration class
class Config :
    # Setting a secret key 
    SECRET_KEY =  os.getenv("APP_SECRET_KEY") 
    # Setting the DB location -- FIXED: was hardcoded to SQLite always,
    # meaning production would silently keep using a local SQLite file
    # inside the container regardless of any MySQL/MariaDB setup.
    # Falls back to SQLite when DATABASE_URL isn't set, preserving the
    # existing local dev experience unchanged.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///site.db")

    # FIXED: check_same_thread/timeout are SQLite-specific connect_args
    # (they come from Python's own sqlite3 module) -- pymysql has no
    # such parameters at all and rejects them outright with
    # "unexpected keyword argument", crashing on startup the moment
    # DATABASE_URL points anywhere other than SQLite. Only apply these
    # when SQLite is actually the active backend.
    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {
                "check_same_thread": False,
                "timeout": 20  # wait for lock instead of immediate failure
            }
        }
    else:
        # FIXED: MariaDB/MySQL closes idle connections after its own
        # wait_timeout (commonly 8 hours by default) -- without these
        # options, SQLAlchemy's connection pool doesn't know a
        # connection died server-side and tries to reuse it anyway on
        # the next request, causing "MySQL server has gone away" /
        # "Connection reset by peer" on the first request after any
        # idle period longer than that timeout.
        #
        # pool_pre_ping: tests each connection with a lightweight query
        # before actually using it for a real request, transparently
        # discarding and replacing it if it's already dead.
        #
        # pool_recycle: proactively recycles any connection older than
        # this many seconds, refreshing it before MySQL's own timeout
        # ever gets the chance to silently kill it server-side.
        # connect_args timeouts: pool_pre_ping's own test query can
        # itself hang indefinitely if the underlying connection is
        # silently dropped (black-holed) rather than cleanly closed --
        # these force pymysql to give up and raise a real, catchable
        # error after a bounded wait, instead of hanging forever. This
        # is what turns "the page spins with a blank white screen
        # forever" into "the page fails fast, then works again on the
        # next attempt once pool_pre_ping discards the bad connection."
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "connect_args": {
                "connect_timeout": 10,
                "read_timeout": 10,
                "write_timeout": 10,
            },
        }

    # responsive user interface
    FLASK_ADMIN_FLUID_LAYOUT = True
    ############ Yahoo SMTP mail server ##################   
    # MAIL_SERVER = "smtp.mail.yahoo.com"
    # MAIL_PORT = 465 
    # MAIL_USE_TLS = False
    # MAIL_USE_SSL = True
    # MAIL_USERNAME = os.getenv("EMAIL_USER") 
    # MAIL_PASSWORD = os.getenv("EMAIL_PASS") 
    ############# Brevo STMP mail Server #################
    MAIL_SERVER = "smtp-relay.brevo.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv("EMAIL_USER")   # your Brevo login email
    MAIL_PASSWORD = os.getenv("EMAIL_PASS")   # the SMTP key, not your account password
    #-------------------------------------------
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    XCHANGE_RATE_API_KEY = os.getenv("XCHANGE_RATE_API_KEY")

    #-------------------------------------------
    # Paystack -- test keys during development, live keys only once
    # Registered Business activation is complete. sk_ vs pk_ and
    # _test_ vs _live_ are baked into the key string itself, so a quick
    # glance confirms which environment is actually configured.
    PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
    PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")

    #-------------------------------------------
    # Image storage backend: 'local' (default, no setup needed for dev)
    # or 'cloudinary' (production). Switching later to another provider
    # (e.g. R2) only ever needs a change in app/services/image_storage.py
    # -- nothing in routes/templates depends on which backend is active.
    IMAGE_BACKEND = os.getenv("IMAGE_BACKEND", "local")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
