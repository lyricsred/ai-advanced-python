from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Link(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(32), unique=True, nullable=False, index=True)
    original_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0)
    last_clicked_at = Column(DateTime, nullable=True)

    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    owner = relationship('User', back_populates='links')
