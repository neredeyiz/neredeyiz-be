import logging
from typing import Dict

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from datetime import date, datetime

from cache import cache
from constants import VOTES_LAST_UPDATED, VOTES
from models import DailyVote

logger = logging.getLogger(__name__)

def sync_votes(db: Session):
    votes_last_updated = cache.get(VOTES_LAST_UPDATED)
    now = datetime.now()
    if votes_last_updated is None or (now - cache.get(VOTES_LAST_UPDATED)).total_seconds() > 5 * 60:
        today = datetime.now().date()

        try:
            for place_name, count in cache.get(VOTES).items():
                stmt = (
                    insert(DailyVote)
                    .values(
                        date=today,
                        place_name=place_name,
                        count=count
                    )
                    .on_conflict_do_update(
                        index_elements=['date', 'place_name'],
                        set_={'count': DailyVote.count + count}
                    )
                )
                db.execute(stmt)
            db.commit()
            cache.update(VOTES_LAST_UPDATED, now)
        except Exception as e:
            logger.error(f"Failed to sync votes: {e}")


def get_today_votes(db: Session, vote_date: date = date.today()) -> Dict[str, int]:
    votes = db.query(DailyVote.place_name, DailyVote.count)\
             .filter(DailyVote.date == vote_date)\
             .all()
    return {place_name: count for place_name, count in votes}