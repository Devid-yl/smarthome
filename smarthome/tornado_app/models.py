from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    """User model - clean Tornado version (no Django leftovers)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(254), nullable=False)
    password = Column(String(128), nullable=False)  # bcrypt hash
    is_active = Column(Boolean, default=True, nullable=False)
    date_joined = Column(DateTime, default=datetime.utcnow, nullable=False)
    profile_image = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)

    houses = relationship("House", back_populates="user")


class House(Base):
    """House model."""
    __tablename__ = "houses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)

    user = relationship("User", back_populates="houses")
    rooms = relationship("Room", back_populates="house")


class Room(Base):
    """Room model."""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    name = Column(String(100), nullable=False)

    house = relationship("House", back_populates="rooms")
