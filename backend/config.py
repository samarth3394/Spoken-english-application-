"""
Aspire English Hub - Configuration Module
==========================================
Centralized configuration management using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Aspire English Hub"
    app_env: str = "development"
    secret_key: str = "change-this-in-production"
    debug: bool = True
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""
    
    # Gemini
    gemini_api_key: str = ""
    
    # URLs
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5500"
    
    # WebRTC
    stun_server: str = "stun:stun.l.google.com:19302"
    turn_server: str = ""
    turn_username: str = ""
    turn_password: str = ""
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
