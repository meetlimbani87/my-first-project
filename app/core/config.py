from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/crime_db"

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    SESSION_EXPIRY_HOURS: int = 24

    # Application
    ENVIRONMENT: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Super Admin Seed
    SUPER_ADMIN_EMAIL: str = "admin@example.com"
    SUPER_ADMIN_PASSWORD: str = "change-me-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
