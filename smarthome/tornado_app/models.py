from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class House(Base):
    """House model.

    Grid format (new layered system):
    Each cell is an object: {
        "base": 0|1|2xxx,  # 0=empty, 1=wall, 2xxx=room
        "sensors": [sensor_ids],  # List of sensor IDs covering this cell
        "equipments": [equipment_ids]  # List of equipment IDs at this cell
    }
    Or legacy format: simple integer array for backwards compatibility
    """

    __tablename__ = "houses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)
    length = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    grid = Column(JSONB, nullable=False)

    user = relationship("User", back_populates="houses")
    rooms = relationship("Room", back_populates="house", cascade="all, delete-orphan")


# 1
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


# 2
class Room(Base):
    """Room model."""

    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    name = Column(String(100), nullable=False)

    house = relationship("House", back_populates="rooms")
    sensors = relationship(
        "Sensor", back_populates="room", cascade="all, delete-orphan"
    )
    equipments = relationship(
        "Equipment", back_populates="room", cascade="all, delete-orphan"
    )


# 3
class Sensor(Base):
    """Sensor model - capteurs simulés."""

    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    # Types: 'temperature', 'luminosity', 'rain', 'presence'
    value = Column(Float, nullable=True)  # Valeur actuelle
    unit = Column(String(20), nullable=True)  # °C, lux, %, etc.
    is_active = Column(Boolean, default=True, nullable=False)
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room = relationship("Room", back_populates="sensors")


# 4
class Equipment(Base):
    """Equipment model - équipements contrôlés."""

    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    # Types: 'shutter', 'door', 'light', 'sound_system'
    state = Column(String(50), default="off", nullable=False)
    # States: 'on'/'off', 'open'/'closed', 0-100 (percentage)
    is_active = Column(Boolean, default=True, nullable=False)
    allowed_roles = Column(JSONB, nullable=True)
    # Rôles autorisés: ['proprietaire', 'admin', 'occupant']
    # Si None/vide, tous peuvent modifier (défaut)
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room = relationship("Room", back_populates="equipments")


# 5
class AutomationRule(Base):
    """Automation Rule model - règles d'automatisation personnalisables."""

    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    name = Column(String(200), nullable=False)  # Nom de la règle
    description = Column(String(500), nullable=True)  # Description
    is_active = Column(Boolean, default=True, nullable=False)

    # Condition (capteur)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    condition_operator = Column(String(10), nullable=False)
    # Opérateurs: '>', '<', '>=', '<=', '==', '!='
    condition_value = Column(Float, nullable=False)

    # Action (équipement)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False)
    action_state = Column(String(50), nullable=False)
    # États: 'on', 'off', 'open', 'closed'

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_triggered = Column(DateTime, nullable=True)

    # Relations
    sensor = relationship("Sensor")
    equipment = relationship("Equipment")


# 6
class HouseMember(Base):
    """House Member model - membres d'une maison avec invitations."""

    __tablename__ = "house_members"

    id = Column(Integer, primary_key=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="occupant", nullable=False)
    # Rôles: 'administrateur', 'occupant'
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    # Statuts: 'pending', 'accepted', 'rejected'

    # Relations
    house = relationship("House")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])


# 7
class EventHistory(Base):
    """Event History model - journalisation des événements."""

    __tablename__ = "event_history"

    id = Column(Integer, primary_key=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    # Types: 'equipment_control', 'sensor_reading', 'member_action',
    #        'automation_triggered', 'house_modified'
    entity_type = Column(String(50), nullable=True)
    # Types: 'equipment', 'sensor', 'member', 'automation_rule',
    #        'house', 'room'
    entity_id = Column(Integer, nullable=True)
    description = Column(String, nullable=False)
    event_metadata = Column(JSONB, nullable=True)
    # Données supplémentaires: ancien/nouveau état, valeurs, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)

    # Relations
    house = relationship("House")
    user = relationship("User")


# 8
class UserPosition(Base):
    """User Position model - position des utilisateurs dans une maison."""

    __tablename__ = "user_positions"

    id = Column(Integer, primary_key=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    x = Column(Integer, nullable=False)  # Position X sur la grille
    y = Column(Integer, nullable=False)  # Position Y sur la grille
    is_active = Column(Boolean, default=True, nullable=False)
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    house = relationship("House")
    user = relationship("User")
