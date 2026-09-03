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
    match_odd = Column(Float, nullable=True)
    profit_loss = Column(Float, nullable=True)
    ai_verdict = Column(String, nullable=True, default='APROVADO')
    ai_confidence = Column(Integer, nullable=True)
    ai_critical_factor = Column(String, nullable=True)
    ai_analysis = Column(String, nullable=True)

    match = relationship("Match", back_populates="predictions")

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    key = Column(String, primary_key=True, index=True)
    value = Column(String)

class RawDataLog(Base):
    __tablename__ = "raw_data_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    source = Column(String, index=True)
    endpoint = Column(String, index=True)
    payload = Column(String) # For huge JSONs, SQLite handles String as unlimited Text

class TeamStatsCache(Base):
    __tablename__ = "team_stats_cache"
    
    team_id = Column(Integer, primary_key=True)
    league_id = Column(Integer, primary_key=True)
    updated_at = Column(DateTime, default=datetime.datetime.now)
    stats_json = Column(String)
