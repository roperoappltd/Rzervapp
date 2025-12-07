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