from flask import Flask
from app.config import Config 
from flask_bcrypt import Bcrypt
#from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_admin import Admin
#from flask_wtf.csrf import CSRFProtect
#from app.csrf import csrf, CSRFError

# Create db object
db = SQLAlchemy()
# Create flask migrate object
migrate = Migrate()
# Create flask mail object
mail = Mail() 
# creating a bcrypt instance for password hashing
bcrypt = Bcrypt()
# initializing csrf
#csrf = CSRFProtect()


# create an instance of loginManager 
#login_manager = LoginManager()
#login_manager.login_view = 'users.login'   # exige login to view the account page
#login_manager.login_message_category = 'info'

# integrate flask admin
#admin = Admin( template_mode='bootstrap4')

def create_app(config_name='default'):

    app = Flask(__name__)
    # Load the proper configuration
    app.config.from_object(Config) #[config_name]
    #csrf.init_app(app)

    with app.app_context():
        # Initialize extensions
        db.init_app(app)
        mail.init_app(app)
        migrate.init_app(app, db)
        bcrypt.init_app(app)
        #login_manager.init_app(app)
        #csrf.init_app(app)

        # Imports our route blueprints
        #from app.enrolls.routes import enrolls
        from app.users.routes import users
        from app.main.routes import main
        #from app.posts.routes import posts
        from app.errors.handlers import errors
        #from app.models import Controller_AdminView

        #from flask_track_usage import TrackUsage
        #from flask_track_usage.storage.sql import SQLStorage

        # initialize the admin controller view
        #admin.init_app(app, index_view=Controller_AdminView())

        # Register our blueprints
        #app.register_blueprint(enrolls)
        app.register_blueprint(users)
        app.register_blueprint(main)
        #app.register_blueprint(posts)
        app.register_blueprint(errors)


        # Create database tables
        db.create_all()

    return app 
