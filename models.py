import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, UniqueConstraint, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Models
class VoteRequest(BaseModel):
    place_name: str

class DailyVote(Base):
    __tablename__ = "daily_votes"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=datetime.date.today, index=True)
    place_name = Column(String, nullable=False)
    count = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint('date', 'place_name', name='uq_date_place'),
    )
class Place(Base):
    __tablename__ = "places"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class AvailableHour(Base):
    __tablename__ = "available_hours"
    id = Column(Integer, primary_key=True, index=True)
    time = Column(String, unique=True, nullable=False)  # e.g., "18:00", "18:30", ...


class DailySelection(Base):
    __tablename__ = "daily_selection"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.date.today, unique=True)
    places = Column(String)  # Comma-separated list of places
    gathering_time = Column(DateTime, nullable=False)
    final_place = Column(String, nullable=True)
