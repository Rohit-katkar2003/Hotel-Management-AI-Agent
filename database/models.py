from sqlalchemy import Integer , Float , Column , String , Float , DateTime , Date , Text , ForeignKey 
from sqlalchemy.orm import relationship 
from datetime import datetime , date 
from .connection import Base


class Customer(Base): 
    __tablename__ = "customers" 

    id = Column(Integer , primary_key=True , autoincrement=True) 
    name = Column(String , nullable=False) 
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="customer") 


class Room(Base): 
    __tablename__ = "rooms" 

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type = Column(String(50), nullable=False)      
    price_per_night = Column(Float, nullable=False)
    capacity = Column(Integer, default=2)
    status = Column(String(20), default="available")     

    bookings = relationship("Booking", back_populates="room")  

class Booking(Base): 
    __tablename__ = "bookings" 

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    status = Column(String(20), default="confirmed")      # confirmed, checked_in, checked_out, cancelled
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking") 


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String(20), nullable=False)            # cash, card, upi
    status = Column(String(20), default="completed")       # completed, pending, failed
    paid_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="payments") 
    
