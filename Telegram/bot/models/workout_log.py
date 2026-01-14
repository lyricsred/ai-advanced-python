from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from bot.config import Base


class WorkoutLog(Base):
    __tablename__ = 'workout_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    workout_type = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    calories_burned = Column(Float, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='workout_logs')

