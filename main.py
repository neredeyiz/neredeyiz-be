import json
import os

import uvicorn
from fastapi import FastAPI, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import datetime

import logging

from fastapi.middleware.cors import CORSMiddleware

from cache import cache
from constants import TODAY_PLACES, GATHERING_TIME, FINAL_PLACE, VOTES
from database import get_db
from models import Base, VoteRequest
from scheduler import create_scheduler
from services.choices import  get_today_selection, get_places_and_gathering_time_from_db
from services.votes import sync_votes, get_today_votes
from utils import _is_within_two_hours_from_now

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = create_scheduler()
scheduler.start()

@app.get("/choices")
def get_choices(db: Session = Depends(get_db)):
    selected_places, gathering_time, votes = cache.get(TODAY_PLACES), cache.get(GATHERING_TIME), cache.get(VOTES)
    if not (selected_places or gathering_time):
        selected_places, gathering_time = get_places_and_gathering_time_from_db(db)
        cache.update_places_and_time(selected_places, gathering_time)
    if not (selected_places and gathering_time):
        return {"message": "No selection made yet."}
    if not votes:
        votes = get_today_votes(db)
        cache.update(VOTES, votes)
    response = {
        TODAY_PLACES: selected_places.split(","),
        GATHERING_TIME: gathering_time,
        VOTES: votes
    }
    if final_place := cache.get(FINAL_PLACE):
        response[FINAL_PLACE] = final_place
    else:
        if _is_within_two_hours_from_now(gathering_time):
            # Unoptimized DB query. We should not re-query the db if we already did above.
            # But that requires a bit of refactor
            today_selection = get_today_selection(db)
            if today_selection and today_selection.final_place:
                response[FINAL_PLACE] = today_selection.final_place
                cache.update(FINAL_PLACE, today_selection.final_place)
    return response

@app.get("/vote")
def vote(place_name: str = Query(..., min_length=1),
         db: Session = Depends(get_db)):
    if not _validate_place_name(place_name):
        return 404
    cache.add_vote(place_name)
    sync_votes(db)
    return cache.get(VOTES)

def _validate_place_name(place_name: str):
    return cache.get(TODAY_PLACES) and place_name in cache.get(TODAY_PLACES).split(",")

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now()}

if __name__ == "__main__":
    uvicorn.run(app, reload=False, log_level=logging.INFO)
