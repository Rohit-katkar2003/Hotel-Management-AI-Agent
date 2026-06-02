from pydantic_settings import BaseSettings , SettingsConfigDict 
import os 
from dotenv import load_dotenv 
load_dotenv() 

class Settings(BaseSettings): 

    open_router_api:str = os.getenv("ROUTER_API_KEY") 
    
    open_router_model : str = "google/gemma-4-31b-it:free" 
    llm_temperature:float=0.1 
    llm_max_tokens:int = 1024 
    llm_streaming:bool=False

    open_router_base_url : str = "https://openrouter.ai/api/v1" 

    # ---- app ----- 
    APP_NAME = "Hotel Management AI Agent"
    APP_VERSION = "1.0.0"

    # ─── Hotel Defaults ───
    DEFAULT_CURRENCY = "USD"
    MAX_BOOKING_DAYS = 30

    HOTEL_DB_PATH = os.getenv("HOTEL_DB_PATH", "hotel.db")
    CHECKPOINT_DB_PATH = os.getenv("CHECKPOINT_DB_PATH", "checkpoints.db")


    debug:bool = True 

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8" , 
        extra="ignore"
    ) 

settings = Settings() 