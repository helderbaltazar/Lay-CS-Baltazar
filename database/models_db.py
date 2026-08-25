from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
import datetime

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, unique=True, index=True)
    date = Column(DateTime, index=True)
    league_name = Column(String)
    home_team = Column(String)
    away_team = Column(String)
    status = Column(String)
    real_score = Column(String, nullable=True)

    predictions = relationship("Prediction", back_populates="match", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    target_score = Column(String, index=True)
    probability = Column(Float)
    rank = Column(Integer)
    is_hit = Column(Boolean, nullable=True)

    match = relationship("Match", back_populates="predictions")
