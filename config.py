import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Determine the user's home directory
home_directory = os.path.expanduser("~")

# Construct the absolute path to the config.txt file in the home directory
config_file_path = os.path.join(home_directory, 'config.txt')

# Load configuration values from the config.txt file
with open(config_file_path, 'r') as config_file:
    for line in config_file:
        key, value = line.strip().split('=')
        app.config[key] = value

login_manager = LoginManager(app)

# assign the db object init
db = SQLAlchemy(app)
migrate = Migrate(app, db)
