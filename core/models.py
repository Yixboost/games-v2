from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String)
    email = Column(String)

    oauth_login_id = Column(
        String,
        unique=True,
        nullable=False,
    )

    oauth_provider = Column(String)
    oauth_subject = Column(String)
    profile_picture_url = Column(String)
    role = Column(String, nullable=False, default="user")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    image_url = Column(String)
    category = Column(String)
