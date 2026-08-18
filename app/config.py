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
        SQLALCHEMY_ENGINE_OPTIONS = {} 

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
    # Image storage backend: 'local' (default, no setup needed for dev)
    # or 'cloudinary' (production). Switching later to another provider
    # (e.g. R2) only ever needs a change in app/services/image_storage.py
    # -- nothing in routes/templates depends on which backend is active.
    IMAGE_BACKEND = os.getenv("IMAGE_BACKEND", "local")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")