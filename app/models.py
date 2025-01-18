from app import db
from datetime import datetime
import pytz

LOCAL_TZ = pytz.timezone("Europe/Berlin")

class FilamentRoll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maker = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    total_weight = db.Column(db.Float, nullable=False)
    remaining_weight = db.Column(db.Float, nullable=False)
    in_use = db.Column(db.Boolean, default=True)

class PrintJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filament_id = db.Column(db.Integer, db.ForeignKey('filament_roll.id'), nullable=False)
    length_used = db.Column(db.Float, nullable=False)
    weight_used = db.Column(db.Float, nullable=False)
    project_name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(LOCAL_TZ))
    filament = db.relationship('FilamentRoll', backref='prints')


    def save(self):
        self.filament.remaining_weight -= self.weight_used
        db.session.add(self)
        db.session.commit()
