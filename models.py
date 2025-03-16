from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Car(db.Model):
    __tablename__ = "cars"

    id = db.Column(db.Integer, primary_key=True, index=True)
    title = db.Column(db.String(255), index=True)
    image = db.Column(db.String(1024))
    images = db.Column(db.String(4096))  # JSON list of images
    price = db.Column(db.Float)
    year = db.Column(db.Integer)
    km = db.Column(db.Integer)
    fuel_type = db.Column(db.String(50))
    transmission = db.Column(db.String(50))
    body_type = db.Column(db.String(50))
    registration_date = db.Column(db.String(50))
    engine_power = db.Column(db.String(50))
    seats = db.Column(db.Integer)
    doors = db.Column(db.Integer)
    color = db.Column(db.String(50))
    condition = db.Column(db.String(50))
    options = db.Column(db.String(4096))  # JSON list of options
    description = db.Column(db.String(4096))
    manual_entry = db.Column(db.Boolean, default=False)

class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True, index=True)
    nome = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    messaggio = db.Column(db.Text, nullable=False)
    auto_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # ensure password hash field has length of at least 256
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)