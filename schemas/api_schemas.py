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

