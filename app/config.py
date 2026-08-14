import os
from dotenv import load_dotenv

load_dotenv()

#----------------------------------------------------------------------------------
# Create configuration class
class Config :
    # Setting a secret key 
    SECRET_KEY =  os.getenv("APP_SECRET_KEY") 
    # Setting the DB location
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db' 
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "check_same_thread": False,
            "timeout": 20  # wait for lock instead of immediate failure
        }
    } 

    # responsive user interface
    FLASK_ADMIN_FLUID_LAYOUT = True

    # Configure  Yahoo SMTP mail server
    MAIL_SERVER = "smtp.mail.yahoo.com"             
    #app.config['MAIL_PORT'] = 587
    MAIL_PORT = 465 
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv("EMAIL_USER") 
    MAIL_PASSWORD = os.getenv("EMAIL_PASS") 

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