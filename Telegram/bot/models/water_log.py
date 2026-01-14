from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from bot.config import Base


class WaterLog(Base):
    __tablename__ = 'water_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='water_logs')

