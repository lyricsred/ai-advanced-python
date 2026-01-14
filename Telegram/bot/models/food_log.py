from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from bot.config import Base


class FoodLog(Base):
    __tablename__ = 'food_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    amount = Column(Float)
    logged_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='food_logs')

