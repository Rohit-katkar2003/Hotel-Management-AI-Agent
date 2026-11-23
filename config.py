from pydantic_settings import BaseSettings , SettingsConfigDict 
from typing import ClassVar 
import os 
from dotenv import load_dotenv 
load_dotenv() 

class Settings(BaseSettings): 

    # ─── Sensnova LLM ─── 
    sensnova_api_key : str = os.getenv("SENSNOVA_API_KEY") 
    sensnova_model : str = "sensenova-6.8-flash-lite" 
    sensnova_base_url : str = "https://token.sensenova.ai/v1" 

    llm_temperature:float=0.1 
    llm_max_tokens:int = 1024 
    llm_streaming:bool=False


    # ---- app ----- 
    APP_NAME:str= "Hotel Management AI Agent"
    APP_VERSION:str = "1.0.0"

    # ─── Hotel Defaults ───
    DEFAULT_CURRENCY: ClassVar[str] = "USD"
    MAX_BOOKING_DAYS: ClassVar[int] = 30

    HOTEL_DB_PATH:str = os.getenv("HOTEL_DB_PATH", "hotel.db")
    CHECKPOINT_DB_PATH:str = os.getenv("CHECKPOINT_DB_PATH", "checkpoints.db")


    debug:bool = True 

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8" , 
        extra="ignore"
    ) 

settings = Settings() 