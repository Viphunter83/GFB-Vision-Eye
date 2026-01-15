from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "GFB-Vision-Eye"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Model Configuration
    MODEL_PATH: str = "models/yolo11n.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_ignore_empty=True,
        extra="ignore"
    )

settings = Settings()
