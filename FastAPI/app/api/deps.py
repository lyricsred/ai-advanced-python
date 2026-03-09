from fastapi import Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import LinkService, UserService


def get_link_service(request: Request, db: Session = None) -> LinkService:
    if db is None:
        db = next(get_db())
    base_url = str(request.base_url).rstrip('/') if request else ''
    return LinkService(db, base_url=base_url)


def get_user_service(db: Session = None) -> UserService:
    if db is None:
        db = next(get_db())
    return UserService(db)
