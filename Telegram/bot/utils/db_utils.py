from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.config import DATABASE_URL, Base


def init_db():
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()

