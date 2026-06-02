from datetime import datetime , date 
from sqlalchemy import (Column , Integer , String , Float , DateTime , Boolean , 
                        ForeignKey , Enum as SQLEnum , Text) 
from sqlalchemy.orm  import relationship 
from enum import Enum 
from database import Base 

class RoomType(str , Enum ): 
    "each room type"
