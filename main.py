import logging
import json
import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import xml.etree.ElementTree as ET
import requests
from models import Car

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db = SQLAlchemy(app)

# Routes
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/car/<int:car_id>')
def car_detail(car_id):
    return render_template("car_detail.html", car_id=car_id)

@app.route('/api/cars/')
def get_cars():
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    search = request.args.get('search', None, type=str)

    query = Car.query
    if search:
        search_filter = or_(
            Car.title.ilike(f"%{search}%"),
            Car.description.ilike(f"%{search}%"),
            Car.color.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    cars = query.offset(skip).limit(limit).all()
    return jsonify([{
        'id': car.id,
        'title': car.title,
        'image': car.image,
        'images': car.images,
        'price': car.price,
        'year': car.year,
        'km': car.km,
        'fuel_type': car.fuel_type,
        'transmission': car.transmission,
        'body_type': car.body_type,
        'registration_date': car.registration_date,
        'engine_power': car.engine_power,
        'seats': car.seats,
        'doors': car.doors,
        'color': car.color,
        'condition': car.condition,
        'options': car.options,
        'description': car.description
    } for car in cars])

@app.route('/api/cars/<int:car_id>')
def get_car(car_id):
    car = Car.query.get_or_404(car_id)
    return jsonify({
        'id': car.id,
        'title': car.title,
        'image': car.image,
        'images': car.images,
        'price': car.price,
        'year': car.year,
        'km': car.km,
        'fuel_type': car.fuel_type,
        'transmission': car.transmission,
        'body_type': car.body_type,
        'registration_date': car.registration_date,
        'engine_power': car.engine_power,
        'seats': car.seats,
        'doors': car.doors,
        'color': car.color,
        'condition': car.condition,
        'options': car.options,
        'description': car.description
    })

@app.route('/api/import-xml/', methods=['POST'])
def import_xml():
    try:
        xml_url = "http://xml.gestionaleauto.com/sarmaservice/export_gestionaleauto.php"
        response = requests.get(xml_url, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        imported_count = 0

        for car_elem in root.findall(".//car"):
            try:
                new_car = Car(
                    title=car_elem.find("title").text or "",
                    image=car_elem.find("image").text or "",
                    images=car_elem.find("images").text if car_elem.find("images") is not None else "[]",
                    price=float(car_elem.find("price").text or 0),
                    year=int(car_elem.find("year").text or 0),
                    km=int(car_elem.find("km").text or 0),
                    fuel_type=car_elem.find("fuel_type").text or "",
                    transmission=car_elem.find("transmission").text or "",
                    body_type=car_elem.find("body_type").text if car_elem.find("body_type") is not None else "",
                    registration_date=car_elem.find("registration_date").text if car_elem.find("registration_date") is not None else "",
                    engine_power=car_elem.find("engine_power").text if car_elem.find("engine_power") is not None else "",
                    seats=int(car_elem.find("seats").text or 0) if car_elem.find("seats") is not None else 0,
                    doors=int(car_elem.find("doors").text or 0) if car_elem.find("doors") is not None else 0,
                    color=car_elem.find("color").text if car_elem.find("color") is not None else "",
                    condition=car_elem.find("condition").text if car_elem.find("condition") is not None else "",
                    options=car_elem.find("options").text if car_elem.find("options") is not None else "[]",
                    description=car_elem.find("description").text if car_elem.find("description") is not None else "",
                )
                db.session.add(new_car)
                imported_count += 1
            except Exception as e:
                logger.error(f"Error importing car: {e}")
                continue

        db.session.commit()
        return jsonify({"message": f"Successfully imported {imported_count} cars"})

    except requests.RequestException as e:
        logger.error(f"Error fetching XML: {e}")
        return jsonify({"error": f"Error fetching XML: {str(e)}"}), 500
    except ET.ParseError as e:
        logger.error(f"Error parsing XML: {e}")
        return jsonify({"error": f"Error parsing XML: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)