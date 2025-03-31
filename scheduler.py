from apscheduler.schedulers.background import BackgroundScheduler

from database import get_db
from services.choices import pick_places, pick_final_place
import logging

logger = logging.getLogger(__name__)

def place_picker():
    db = next(get_db())
    try:
        pick_places(db)
    except Exception as e:
        logger.error(f"Error in midnight places selection: {e}")
    finally:
        db.close()

def create_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        place_picker,
        "interval",
        minutes=15,
        id="places_selection"
    )

    # Frequent check - pick final place
    scheduler.add_job(
        pick_final_place,
        "interval",
        minutes=15,
        id="final_place_selection"
    )

    return scheduler