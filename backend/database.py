"""SQLite engine/session setup for Leavely."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "leavely.db")
# Allow overriding where the SQLite file lives (e.g. local disk instead of a
# network-mounted project folder, which some filesystems don't support for
# SQLite's file locking).
DB_PATH = os.environ.get("LEAVELY_DB_PATH", DEFAULT_DB_PATH)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401  (ensures models are registered on Base)
    Base.metadata.create_all(bind=engine)
