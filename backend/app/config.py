"""Application configuration settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/autobox"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000, http://43.201.254.235 , https://autoboxx.duckdns.org"
    
    # MQTT Configuration
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC_PREFIX: str = "factory_msg"
    MQTT_CLIENT_ID: str = "autobox-backend"
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_ENABLED: bool = True
    
    # MQTT TLS Configuration (for external connections)
    MQTT_USE_TLS: bool = False
    MQTT_CA_CERT: str = ""
    MQTT_CLIENT_CERT: str = ""
    MQTT_CLIENT_KEY: str = ""
    MQTT_TLS_INSECURE: bool = False  # Set to True to skip hostname verification
    
    # Raspberry Pi REST API
    RASPBERRY_PI_URL: str = "http://localhost:5000"
    
    # OCR Configuration
    OCR_ENABLED: bool = True
    OCR_API_URL: str = "https://9d96-2001-2d8-7444-2e40-c943-2d5c-33e8-b3d8.ngrok-free.app/predict/base64"
    OCR_WATCH_DIR: str = "./data"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
