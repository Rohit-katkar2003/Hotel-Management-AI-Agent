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

    