import logging
import json
import os
from flask import render_template, jsonify, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import xml.etree.ElementTree as ET
import requests
from flask_login import LoginManager, login_user, login_required, current_user
from app import create_app, db
from models import Car, Contact, User
from scheduler import init_scheduler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = create_app()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f'/static/uploads/{filename}'
    return None

@app.route('/api/cars/manual', methods=['POST'])
@login_required
def create_car():
    try:
        # Debug logging
        logger.info("Received form data:")
        logger.info(f"Form data: {request.form}")
        logger.info(f"Files: {request.files}")

        # Handle main image
        main_image = request.files.get('image')
        main_image_path = save_uploaded_file(main_image) if main_image else ''
        logger.info(f"Main image path: {main_image_path}")

        # Handle gallery images
        gallery_images = request.files.getlist('gallery_images')
        gallery_paths = []
        for image in gallery_images:
            path = save_uploaded_file(image)
            if path:
                gallery_paths.append(path)
        logger.info(f"Gallery paths: {gallery_paths}")

        # Get other form data
        data = request.form
        try:
            price = float(data['price']) if data['price'] else 0.0
            year = int(data['year']) if data['year'] else 0
            km = int(data['km']) if data['km'] else 0
            seats = int(data['seats']) if data['seats'] else 0
            doors = int(data['doors']) if data['doors'] else 0
        except (ValueError, KeyError) as e:
            logger.error(f"Error converting numeric values: {e}")
            return jsonify({"error": "Errore nei valori numerici"}), 400

        # Parse options
        options = data.getlist('options[]') if 'options[]' in data else []
        if not options and 'options' in data:
            options = [opt.strip() for opt in data['options'].split('\n') if opt.strip()]
        logger.info(f"Parsed options: {options}")

        new_car = Car(
            title=data['title'],
            price=price,
            year=year,
            km=km,
            fuel_type=data['fuel_type'],
            transmission=data['transmission'],
            body_type=data['body_type'],
            registration_date=data.get('registration_date', ''),
            engine_power=data.get('engine_power', ''),
            seats=seats,
            doors=doors,
            color=data.get('color', ''),
            condition=data.get('condition', 'Usato'),
            options=json.dumps(options),
            description=data.get('description', ''),
            manual_entry=True,
            image=main_image_path,
            images=json.dumps(gallery_paths)
        )

        db.session.add(new_car)
        db.session.commit()
        logger.info(f"Successfully created car with ID: {new_car.id}")

        return jsonify({"message": "Auto aggiunta con successo", "id": new_car.id}), 201

    except Exception as e:
        logger.error(f"Error creating car: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logger.info(f"Login attempt for username: {username}")

        user = User.query.filter_by(username=username).first()
        if user:
            logger.info("User found in database")
            if user.check_password(password):
                logger.info("Password check successful")
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                logger.warning("Password check failed")
        else:
            logger.warning(f"No user found with username: {username}")

        flash('Invalid username or password')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/car/<int:car_id>')
def car_detail(car_id):
    car = Car.query.get(car_id)
    if car is None:
        return render_template("404.html"), 404
    return render_template("car_detail.html", car_id=car_id)

@app.route('/api/contacts/', methods=['POST'])
def create_contact():
    try:
        data = request.get_json()
        if not all(key in data for key in ['nome', 'telefono', 'messaggio', 'auto_id']):
            return jsonify({"error": "Dati mancanti"}), 400

        car = Car.query.get(data['auto_id'])
        if not car:
            return jsonify({"error": "Auto non trovata"}), 404

        new_contact = Contact(
            nome=data['nome'],
            telefono=data['telefono'],
            messaggio=data['messaggio'],
            auto_id=data['auto_id']
        )

        db.session.add(new_contact)
        db.session.commit()

        return jsonify({"message": "Richiesta inviata con successo"}), 201

    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        db.session.rollback()
        return jsonify({"error": "Errore durante l'invio della richiesta"}), 500

@app.route('/api/cars/')
def get_cars():
    try:
        # Pagination parameters
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)

        # Filter parameters
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        min_year = request.args.get('min_year', type=int)
        max_year = request.args.get('max_year', type=int)
        min_km = request.args.get('min_km', type=int)
        max_km = request.args.get('max_km', type=int)
        fuel_type = request.args.get('fuel_type', type=str)
        transmission = request.args.get('transmission', type=str)
        body_type = request.args.get('body_type', type=str)

        # Build query
        query = Car.query

        # Apply filters
        if min_price is not None:
            query = query.filter(Car.price >= min_price)
        if max_price is not None:
            query = query.filter(Car.price <= max_price)
        if min_year is not None:
            query = query.filter(Car.year >= min_year)
        if max_year is not None:
            query = query.filter(Car.year <= max_year)
        if min_km is not None:
            query = query.filter(Car.km >= min_km)
        if max_km is not None:
            query = query.filter(Car.km <= max_km)
        if fuel_type:
            query = query.filter(Car.fuel_type.ilike(f"%{fuel_type}%"))
        if transmission:
            query = query.filter(Car.transmission.ilike(f"%{transmission}%"))
        if body_type:
            if body_type == "4/5 Porte":
                query = query.filter(or_(
                    Car.body_type.ilike("%4/5 Porte%"),
                    Car.body_type.ilike("%4/5-Porte%")
                ))
            elif body_type == "2/3 Porte":
                query = query.filter(or_(
                    Car.body_type.ilike("%2/3 Porte%"),
                    Car.body_type.ilike("%2/3-Porte%")
                ))
            else:
                query = query.filter(Car.body_type.ilike(f"%{body_type}%"))

        # Execute query with pagination
        cars = query.offset(skip).limit(limit).all()

        # Convert to JSON
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
        return jsonify({"error": "Auto non trovata"}), 404

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

        # Delete only non-manual cars before import
        Car.query.filter_by(manual_entry=False).delete()
        db.session.commit() #added commit here to clear before import

        for car_elem in root.findall(".//car"):
            try:
                # Extract images
                images = []
                for img in car_elem.findall("images/image"):
                    big_img = img.find("big")
                    if big_img is not None and big_img.text:
                        images.append(big_img.text)

                # Extract options
                options = []
                for opt in car_elem.findall("options/standard_option"):
                    if opt is not None and opt.text:
                        options.append(opt.text)

                # Get model info
                model_elem = car_elem.find("model")
                if model_elem is None:
                    logger.warning("Skipping car: Missing model element")
                    errors_count += 1
                    continue

                make = model_elem.find("make")
                model = model_elem.find("model")
                version = model_elem.find("version")

                if not all([make is not None and make.text, 
                          model is not None and model.text,
                          version is not None and version.text]):
                    logger.warning("Skipping car: Missing make/model/version info")
                    errors_count += 1
                    continue

                title = f"{make.text} {model.text} {version.text}"

                # Get numeric values safely
                try:
                    price = float(car_elem.find("customers_price").text)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid price for car {title}: {e}")
                    price = 0.0

                try:
                    reg_date = car_elem.find("registration_date")
                    if reg_date is not None and reg_date.text:
                        # Formato: MM/YYYY
                        year = int(reg_date.text.split('/')[-1])
                    else:
                        year = 0
                except (ValueError, IndexError) as e:
                    logger.warning(f"Invalid registration date for car {title}: {e}")
                    year = 0

                try:
                    km = int(car_elem.find("km").text)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid km for car {title}: {e}")
                    km = 0

                new_car = Car(
                    title=title,
                    image=images[0] if images else "",
                    images=json.dumps(images),
                    price=price,
                    year=year,
                    km=km,
                    fuel_type=model_elem.find("fuel").text if model_elem.find("fuel") is not None else "",
                    transmission=car_elem.find("gearbox").text if car_elem.find("gearbox") is not None else "",
                    body_type=model_elem.find("body").text if model_elem.find("body") is not None else "",
                    registration_date=car_elem.find("registration_date").text if car_elem.find("registration_date") is not None else "",
                    engine_power=model_elem.find("kwatt").text if model_elem.find("kwatt") is not None else "",
                    seats=int(car_elem.find("seats").text) if car_elem.find("seats") is not None and car_elem.find("seats").text else 0,
                    doors=int(car_elem.find("doors").text) if car_elem.find("doors") is not None and car_elem.find("doors").text else 0,
                    color=car_elem.find("exterior/color").text if car_elem.find("exterior/color") is not None else "",
                    condition=car_elem.find("usage").text if car_elem.find("usage") is not None else "",
                    options=json.dumps(options),
                    description=car_elem.find("formatted_additional_informations").text if car_elem.find("formatted_additional_informations") is not None else "",
                    manual_entry=False
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/api/cars/manual', methods=['GET'])
@login_required
def get_manual_cars():
    try:
        cars = Car.query.filter_by(manual_entry=True).all()
        return jsonify([{
            'id': car.id,
            'title': car.title,
            'price': car.price,
            'year': car.year,
            'km': car.km,
            'image': car.image
        } for car in cars])
    except Exception as e:
        logger.error(f"Error getting manual cars: {e}")
        return jsonify({"error": "Error retrieving manual cars"}), 500

@app.route('/api/cars/<int:car_id>', methods=['DELETE'])
@login_required
def delete_car(car_id):
    try:
        car = Car.query.get_or_404(car_id)

        # Verifica che l'auto sia stata inserita manualmente
        if not car.manual_entry:
            return jsonify({"error": "Non puoi eliminare un'auto importata da XML"}), 403

        # Elimina le immagini dal filesystem
        if car.image and car.image.startswith('/static/uploads/'):
            try:
                os.remove(car.image.lstrip('/'))
            except OSError:
                logger.warning(f"Could not delete image file: {car.image}")

        if car.images:
            try:
                gallery_images = json.loads(car.images)
                for img in gallery_images:
                    if img.startswith('/static/uploads/'):
                        try:
                            os.remove(img.lstrip('/'))
                        except OSError:
                            logger.warning(f"Could not delete gallery image file: {img}")
            except json.JSONDecodeError:
                logger.warning(f"Could not parse gallery images JSON for car {car_id}")

        db.session.delete(car)
        db.session.commit()
        return jsonify({"message": "Auto eliminata con successo"})
    except Exception as e:
        logger.error(f"Error deleting car {car_id}: {e}")
        db.session.rollback()
        return jsonify({"error": "Errore durante l'eliminazione dell'auto"}), 500

@app.route('/api/cars/<int:car_id>', methods=['PUT'])
@login_required
def update_car(car_id):
    try:
        car = Car.query.get_or_404(car_id)

        # Verifica che l'auto sia stata inserita manualmente
        if not car.manual_entry:
            return jsonify({"error": "Non puoi modificare un'auto importata da XML"}), 403

        # Handle main image
        main_image = request.files.get('image')
        if main_image:
            # Delete old image if it exists and is in uploads folder
            if car.image and car.image.startswith('/static/uploads/'):
                try:
                    os.remove(car.image.lstrip('/'))
                except OSError:
                    logger.warning(f"Could not delete old image file: {car.image}")

            main_image_path = save_uploaded_file(main_image)
            if main_image_path:
                car.image = main_image_path

        # Handle gallery images
        gallery_images = request.files.getlist('gallery_images')
        if gallery_images:
            # Delete old gallery images if they exist and are in uploads folder
            if car.images:
                try:
                    old_gallery = json.loads(car.images)
                    for img in old_gallery:
                        if img.startswith('/static/uploads/'):
                            try:
                                os.remove(img.lstrip('/'))
                            except OSError:
                                logger.warning(f"Could not delete old gallery image file: {img}")
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse old gallery images JSON for car {car_id}")

            # Save new gallery images
            gallery_paths = []
            for image in gallery_images:
                path = save_uploaded_file(image)
                if path:
                    gallery_paths.append(path)
            car.images = json.dumps(gallery_paths)

        # Update other fields
        data = request.form
        try:
            if data.get('price'):
                car.price = float(data['price'])
            if data.get('year'):
                car.year = int(data['year'])
            if data.get('km'):
                car.km = int(data['km'])
            if data.get('seats'):
                car.seats = int(data['seats'])
            if data.get('doors'):
                car.doors = int(data['doors'])
        except (ValueError, KeyError) as e:
            logger.error(f"Error converting numeric values: {e}")
            return jsonify({"error": "Errore nei valori numerici"}), 400

        # Update text fields
        car.title = data.get('title', car.title)
        car.fuel_type = data.get('fuel_type', car.fuel_type)
        car.transmission = data.get('transmission', car.transmission)
        car.body_type = data.get('body_type', car.body_type)
        car.registration_date = data.get('registration_date', car.registration_date)
        car.engine_power = data.get('engine_power', car.engine_power)
        car.color = data.get('color', car.color)

        # Handle options
        options = data.getlist('options[]')
        if not options and 'options' in data:
            options = [opt.strip() for opt in data['options'].split('\n') if opt.strip()]
        car.options = json.dumps(options)

        car.description = data.get('description', car.description)

        db.session.commit()
        logger.info(f"Successfully updated car with ID: {car.id}")

        return jsonify({"message": "Auto aggiornata con successo"}), 200

    except Exception as e:
        logger.error(f"Error updating car {car_id}: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)