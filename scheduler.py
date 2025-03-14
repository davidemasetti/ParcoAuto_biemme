from apscheduler.schedulers.background import BackgroundScheduler
import logging
import threading
import time
import xml.etree.ElementTree as ET
import requests
import json
from datetime import datetime
from app import create_app
from models import Car

logger = logging.getLogger(__name__)
app = create_app()

def import_xml():
    """
    Funzione per importare i dati dal feed XML.
    Viene eseguita automaticamente ogni 24 ore.
    """
    logger.info("🔄 Importazione XML automatica in corso...")
    try:
        with app.app_context():
            xml_url = "http://xml.gestionaleauto.com/sarmaservice/export_gestionaleauto.php"
            response = requests.get(xml_url, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            imported_count = 0
            errors_count = 0

            # Rimuovi tutte le auto esistenti per evitare duplicati
            Car.query.delete()

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
                        description=car_elem.find("formatted_additional_informations").text if car_elem.find("formatted_additional_informations") is not None else ""
                    )

                    logger.info(f"Importing car: {new_car.title} (Year: {new_car.year}, Price: {new_car.price})")
                    app.db.session.add(new_car)
                    imported_count += 1

                except Exception as e:
                    logger.error(f"Error importing car: {e}")
                    errors_count += 1
                    continue

            app.db.session.commit()
            message = f"✅ Importazione automatica completata: {imported_count} auto importate"
            if errors_count > 0:
                message += f" ({errors_count} errori riscontrati)"
            logger.info(message)

    except Exception as e:
        logger.error(f"❌ Errore durante l'importazione automatica: {e}")


def delayed_scheduler_start():
    """
    Avvia lo scheduler in un thread separato con un ritardo iniziale
    per evitare blocchi durante l'avvio dell'applicazione
    """
    try:
        # Attendi 10 secondi prima di avviare lo scheduler
        time.sleep(10)

        logger.info("Inizializzazione scheduler...")
        scheduler = BackgroundScheduler()

        # Aggiungi il job per l'importazione XML ogni 24 ore
        # con esecuzione immediata
        scheduler.add_job(
            import_xml,
            'interval',
            hours=24,
            id='xml_import',
            next_run_time=datetime.now()  # Esegui subito la prima volta
        )

        scheduler.start()
        logger.info("Scheduler avviato con successo")

    except Exception as e:
        logger.error(f"Errore nell'avvio dello scheduler: {e}")

def init_scheduler():
    """
    Inizializza lo scheduler in un thread separato
    """
    thread = threading.Thread(target=delayed_scheduler_start, daemon=True)
    thread.start()
    logger.info("Thread scheduler avviato")
    return thread