from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, date
import random
import logging

from cache import cache
from constants import FINAL_PLACE, TODAY_PLACES, GATHERING_TIME, turkey_tz, CACHE_DATE
from database import get_db
from utils import _is_within_two_hours_from_now
from models import DailySelection, Place, AvailableHour

logger = logging.getLogger(__name__)


def get_available_places(db: Session):
    return [place.name for place in db.query(Place).all()]

def get_available_hours(db: Session):
    return [hour.time for hour in db.query(AvailableHour).all()]


def get_today_selection(db: Session):
    return db.query(DailySelection).filter(
        func.date(DailySelection.date) == date.today()).first()

def pick_places(db: Session):
    today = datetime.today()
    if today == cache.get(CACHE_DATE):
        return
    today_selection = get_today_selection(db)
    if today_selection:
        cache.update(CACHE_DATE, today)
        return
    cache.reset()
    available_places = get_available_places(db)
    available_hours = get_available_hours(db)

    if not available_places or not available_hours:
        logger.error("No places or available hours found.")
        return

    num_places = random.randint(3, 5)
    selected_places = random.sample(available_places, num_places)
    gathering_time_str = random.choice(available_hours)
    gathering_time = datetime.strptime(gathering_time_str, "%H:%M").time()
    logger.info(f"Selected places for today: {selected_places}, gathering time is: {gathering_time}")
    store_selection(db, selected_places, gathering_time)
    cache.update(CACHE_DATE, today)
    return selected_places, gathering_time


def store_selection(db: Session, selected_places: list, gathering_time: datetime.time):
    selection = DailySelection(
        places=",".join(selected_places),
        gathering_time=datetime.combine(date.today(), gathering_time)
    )
    db.add(selection)
    db.commit()
    return selection

def pick_final_place():
    if cache.get(FINAL_PLACE):
        logger.info("Final place already selected.")
        return

    db = next(get_db())
    selected_places, gathering_time = cache.get(TODAY_PLACES), cache.get(GATHERING_TIME)
    if not (selected_places and gathering_time):
        selected_places, gathering_time = get_places_and_gathering_time_from_db(db)
        cache.update_places_and_time(selected_places, gathering_time)
    if not (selected_places and gathering_time):
        logger.error("Error getting today's selections")
        db.close()
        raise

    if _is_within_two_hours_from_now(gathering_time):
        _set_final_place(db, selected_places)

def get_places_and_gathering_time_from_db(db):
    try:
        today_selection = get_today_selection(db)
        if not today_selection:
            pick_places(db)
        today_selection = get_today_selection(db)
        return today_selection.places, today_selection.gathering_time
    except Exception as e:
        logger.error(f"Error getting today's selection: {e}")
        raise

def _set_final_place(db, selected_places):
    try:
        final_place = random.choice(selected_places.split(","))
        logger.info(f"Final place selected: {final_place}")
        cache.update(FINAL_PLACE, final_place)
        today_selection = get_today_selection(db)
        today_selection.final_place = final_place
        db.commit()
        db.refresh(today_selection)
    except Exception as e:
        logger.error(f"Error setting final place to database: {e}")
        raise
    finally:
        db.close()
