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
        logger.info(f"Fetching XML from {xml_url}")
        response = requests.get(xml_url, timeout=10)
        response.raise_for_status()

        logger.debug(f"XML Response: {response.text[:1000]}...")  # Log first 1000 chars of response
        root = ET.fromstring(response.content)
        imported_count = 0
        errors_count = 0

        for car_elem in root.findall(".//car"):
            try:
                # Log raw XML data for debugging
                car_xml = ET.tostring(car_elem, encoding='unicode')
                logger.debug(f"Processing car XML: {car_xml}")

                # Extract images
                images = []
                for img in car_elem.findall("images/image"):
                    if img.find("big") is not None and img.find("big").text:
                        images.append(img.find("big").text)

                # Extract options
                options = []
                for opt in car_elem.findall("options/standard_option"):
                    if opt is not None and opt.text:
                        options.append(opt.text)

                # Get model info
                make = car_elem.find("model/make")
                model = car_elem.find("model/model")
                version = car_elem.find("model/version")

                if not all([make, model, version]):
                    logger.warning("Skipping car: Missing make/model/version info")
                    errors_count += 1
                    continue

                title = f"{make.text} {model.text} {version.text}"

                # Get numeric values safely
                try:
                    price = float(car_elem.find("customers_price").text)
                except (ValueError, AttributeError):
                    logger.warning(f"Invalid price for car {title}")
                    price = 0.0

                try:
                    registration_date = car_elem.find("registration_date").text
                    if registration_date:
                        year = int(registration_date.split('/')[-1])
                        if year < 1900 or year > 2100:
                            raise ValueError(f"Invalid year: {year}")
                    else:
                        raise ValueError("Empty registration date")
                except (ValueError, AttributeError, IndexError) as e:
                    logger.warning(f"Invalid year for car {title}: {str(e)}")
                    year = 0

                try:
                    km = int(car_elem.find("km").text)
                except (ValueError, AttributeError):
                    logger.warning(f"Invalid km for car {title}")
                    km = 0

                # Create car with validated data
                new_car = Car(
                    title=title,
                    image=images[0] if images else "",
                    images=json.dumps(images),
                    price=price,
                    year=year,
                    km=km,
                    fuel_type=car_elem.find("fuel").text if car_elem.find("fuel") is not None else "",
                    transmission=car_elem.find("gearbox").text if car_elem.find("gearbox") is not None else "",
                    body_type=car_elem.find("model/body").text if car_elem.find("model/body") is not None else "",
                    registration_date=car_elem.find("registration_date").text if car_elem.find("registration_date") is not None else "",
                    engine_power=car_elem.find("model/kwatt").text if car_elem.find("model/kwatt") is not None else "",
                    seats=int(car_elem.find("seats").text) if car_elem.find("seats") is not None and car_elem.find("seats").text else 0,
                    doors=int(car_elem.find("doors").text) if car_elem.find("doors") is not None and car_elem.find("doors").text else 0,
                    color=car_elem.find("exterior/color").text if car_elem.find("exterior/color") is not None else "",
                    condition=car_elem.find("condition").text if car_elem.find("condition") is not None else "",
                    options=json.dumps(options),
                    description=car_elem.find("formatted_additional_informations").text if car_elem.find("formatted_additional_informations") is not None else ""
                )

                logger.info(f"Importing car: {new_car.title} (Year: {new_car.year}, Price: {new_car.price})")
                db.session.add(new_car)
                imported_count += 1

            except Exception as e:
                logger.error(f"Error importing car: {e}")
                errors_count += 1
                continue

        db.session.commit()
        message = f"Successfully imported {imported_count} cars"
        if errors_count > 0:
            message += f" ({errors_count} errors encountered)"
        logger.info(message)
        return jsonify({"message": message})

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