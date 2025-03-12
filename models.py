from app import db

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