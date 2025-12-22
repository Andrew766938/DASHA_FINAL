from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class TrainType(str, enum.Enum):
    PLATZKART = "platzkart"  # Плацкарт
    COUPE = "coupe"  # Купе
    SUITE = "suite"  # Люкс

class DiscountType(str, enum.Enum):
    CHILD = "child"  # Детский
    STUDENT = "student"  # Студенческий
    PENSIONER = "pensioner"  # Пенсионер
    NONE = "none"  # Без скидки

class Train(Base):
    __tablename__ = "trains"
    
    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String(50), unique=True, index=True)
    route_from = Column(String(100), index=True)
    route_to = Column(String(100), index=True)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    duration_hours = Column(Integer)
    base_price = Column(Float)  # Базовая цена за место
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Wagon(Base):
    __tablename__ = "wagons"
    
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"), index=True)
    wagon_number = Column(Integer)
    wagon_type = Column(String(20))  # platzkart, coupe, suite
    total_seats = Column(Integer)
    price_multiplier = Column(Float, default=1.0)  # Множитель цены в зависимости от типа
    created_at = Column(DateTime, default=datetime.utcnow)

class Seat(Base):
    __tablename__ = "seats"
    
    id = Column(Integer, primary_key=True, index=True)
    wagon_id = Column(Integer, ForeignKey("wagons.id"), index=True)
    seat_number = Column(Integer)
    is_available = Column(Boolean, default=True)
    is_reserved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"), index=True)
    wagon_id = Column(Integer, ForeignKey("wagons.id"), index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"), index=True)
    passenger_name = Column(String(200))
    passenger_email = Column(String(200))
    passenger_phone = Column(String(20))
    discount_type = Column(String(20), default="none")
    discount_percent = Column(Float, default=0.0)
    base_price = Column(Float)
    final_price = Column(Float)
    ticket_number = Column(String(50), unique=True, index=True)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
