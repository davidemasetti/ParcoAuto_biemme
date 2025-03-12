import logging
import json
import os
from flask import render_template, jsonify, request
from sqlalchemy import or_
import xml.etree.ElementTree as ET
import requests
from app import create_app, db
from models import Car

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = create_app()

# Routes
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/car/<int:car_id>')
def car_detail(car_id):
    return render_template("car_detail.html", car_id=car_id)

@app.route('/api/cars/')
def get_cars():
    try:
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
    except Exception as e:
        logger.error(f"Error getting cars: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/cars/<int:car_id>')
def get_car(car_id):
    try:
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
    except Exception as e:
        logger.error(f"Error getting car {car_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

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
                # Get values with safe fallbacks
                def get_text(elem, path, default=""):
                    node = elem.find(path)
                    return node.text if node is not None and node.text is not None else default

                def get_int(elem, path, default=0):
                    text = get_text(elem, path, str(default))
                    try:
                        return int(text)
                    except (ValueError, TypeError):
                        return default

                def get_float(elem, path, default=0.0):
                    text = get_text(elem, path, str(default))
                    try:
                        return float(text)
                    except (ValueError, TypeError):
                        return default

                new_car = Car(
                    title=get_text(car_elem, "title"),
                    image=get_text(car_elem, "image"),
                    images=get_text(car_elem, "images", "[]"),
                    price=get_float(car_elem, "price"),
                    year=get_int(car_elem, "year"),
                    km=get_int(car_elem, "km"),
                    fuel_type=get_text(car_elem, "fuel_type"),
                    transmission=get_text(car_elem, "transmission"),
                    body_type=get_text(car_elem, "body_type"),
                    registration_date=get_text(car_elem, "registration_date"),
                    engine_power=get_text(car_elem, "engine_power"),
                    seats=get_int(car_elem, "seats"),
                    doors=get_int(car_elem, "doors"),
                    color=get_text(car_elem, "color"),
                    condition=get_text(car_elem, "condition"),
                    options=get_text(car_elem, "options", "[]"),
                    description=get_text(car_elem, "description")
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