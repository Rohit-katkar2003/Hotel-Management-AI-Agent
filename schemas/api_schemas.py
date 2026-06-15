from pydantic import BaseModel , EmailStr 
from typing import Optional 
from datetime import date  , datetime 

# chat  
class ChatRequest(BaseModel): 
    message : str 
    thread_id : Optional[str] = None 

class ChatResponse(BaseModel): 
    reply : str 
    thread_id : str 

    
## customer  

class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: str
    address: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(BaseModel): 
    id: int
    name: str
    email: str
    phone: str
    address: Optional[str]
    created_at: datetime 


# ─── Room ───
class RoomResponse(BaseModel):
    id: int
    room_number: str
    room_type: str
    price_per_night: float
    capacity: int
    status: str


# ─── Booking ───
class BookingCreate(BaseModel):
    customer_id: int
    room_id: int
    check_in: date
    check_out: date

class BookingResponse(BaseModel):
    id: int
    customer_id: int
    room_id: int
    check_in: date
    check_out: date
    status: str
    total_amount: float


# ─── Payment ───
class PaymentRequest(BaseModel):
    booking_id: int
    amount: float
    method: str = "card"  # cash, card, upi

class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: float
    method: str
    status: str
    paid_at: datetime