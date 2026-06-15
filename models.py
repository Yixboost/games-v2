from sqlalchemy import Column, Integer, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    oauth_login_id = Column(
        String,
        unique=True,
        nullable=False
    )

    profile_picture_url = Column(String)


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    image_url = Column(String)

    category = Column(String)