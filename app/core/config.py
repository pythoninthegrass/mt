"""Configuration module for FastAPI backend."""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "MT Music Player"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Server
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 3000
    
    # Database
    DATABASE_URL: str = "sqlite:///./mt_music.db"
    DATABASE_ECHO: bool = False
    
    # Redis (for caching and WebSocket pub/sub)
    REDIS_URL: str | None = None
    
    # CORS
    CORS_ENABLED: bool = True
    CORS_ORIGINS: list[str] = ["*"]
    
    # WebSocket
    WS_MESSAGE_QUEUE_SIZE: int = 100
    
    # File paths
    MUSIC_LIBRARY_PATH: Path = Path.home() / "Music"
    CACHE_DIR: Path = Path.home() / ".mt" / "cache"
    
    # Background tasks
    SCAN_CHUNK_SIZE: int = 100
    SCAN_TIMEOUT: int = 300  # seconds
    
    class Config:
        """Pydantic config."""
        
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()