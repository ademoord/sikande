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

# Production uses config.txt (MySQL). If it is missing we are running locally,
# so we fall back to a self-contained SQLite database with placeholder data.
if os.path.exists(config_file_path):
    # Load configuration values from the config.txt file (production server)
    with open(config_file_path, 'r') as config_file:
        for line in config_file:
            line = line.strip()
            if not line or '=' not in line:
                continue
            key, value = line.split('=', 1)
            app.config[key] = value
else:
    # Local development fallback: use a local SQLite database.
    base_dir = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)

    app.config['LOCAL_DEV'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(data_dir, 'local.sqlite3')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'local-dev-secret-key'
    app.config['GOLD_API_BASE_URL'] = os.environ.get(
        'GOLD_API_BASE_URL', 'https://logam-mulia-api.iamutaki.workers.dev')

login_manager = LoginManager(app)

# assign the db object init
db = SQLAlchemy(app)
migrate = Migrate(app, db)
