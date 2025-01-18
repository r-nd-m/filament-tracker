from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object("config.Config")

# Disable template caching
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models
