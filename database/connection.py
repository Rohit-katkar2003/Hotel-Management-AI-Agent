from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker , declarative_base 
from config import settings 

engine = create_engine(url=f"sqlite:///{settings.HOTEL_DB_PATH}" , 
                       connect_args={"check_same_thread":False} , 
                       echo=False) 

# create new session per operation 
SessionLocal = sessionmaker(bind=engine , autocommit=False , autoflush=False) 

Base = declarative_base()