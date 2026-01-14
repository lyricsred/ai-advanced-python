from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from bot.config import Base


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    weight = Column(Float)
    height = Column(Float)
    age = Column(Integer)
    gender = Column(String)
    activity_minutes = Column(Integer)
    city = Column(String)
    calorie_goal = Column(Float)
    water_goal = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    water_logs = relationship('WaterLog', back_populates='user', cascade='all, delete-orphan')
    food_logs = relationship('FoodLog', back_populates='user', cascade='all, delete-orphan')
    workout_logs = relationship('WorkoutLog', back_populates='user', cascade='all, delete-orphan')

