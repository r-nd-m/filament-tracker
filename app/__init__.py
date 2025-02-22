import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
static_folder = os.path.join(base_dir, 'static')

app = Flask(__name__, static_folder=static_folder)
app.config.from_object("config.Config")

# Disable template caching
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models
