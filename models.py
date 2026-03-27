import os
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# External URL — для локального бота
# Internal URL — для Render Web Service (через переменную окружения)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://beton_db_wcnd_user:YtIJ4poaTVGtXzONVCC8yHL3zRWkv3EE@dpg-d73e4nv5r7bs73fj42vg-a.virginia-postgres.render.com/beton_db_wcnd"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    events = relationship("Event", back_populates="owner")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="events")
    participants = relationship("EventParticipant", back_populates="event")


class EventParticipant(Base):
    __tablename__ = "event_participants"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="going")

    event = relationship("Event", back_populates="participants")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()