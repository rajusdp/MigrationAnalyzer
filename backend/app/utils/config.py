"""
Application configuration using Pydantic Settings
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:pass@localhost:5432/migration_estimator",
        description="PostgreSQL database URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    
    # Security
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT signing secret"
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # Azure Services
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(
        default=None,
        description="Azure Blob Storage connection string"
    )
    AZURE_STORAGE_CONTAINER_NAME: str = Field(
        default="migration-reports",
        description="Azure Blob Storage container for PDFs"
    )
    
    # Azure AD B2C
    AZURE_AD_B2C_TENANT_ID: Optional[str] = Field(default=None)
    AZURE_AD_B2C_CLIENT_ID: Optional[str] = Field(default=None)
    AZURE_AD_B2C_CLIENT_SECRET: Optional[str] = Field(default=None)
    AZURE_AD_B2C_AUTHORITY: Optional[str] = Field(default=None)
    
    # External Services
    SENDGRID_API_KEY: Optional[str] = Field(default=None)
    APPLICATION_INSIGHTS_KEY: Optional[str] = Field(default=None)
    
    # Feature Flags
    ENABLE_PDF_GENERATION: bool = Field(default=True)
    ENABLE_EMAIL_NOTIFICATIONS: bool = Field(default=True)
    ENABLE_RATE_LIMITING: bool = Field(default=True)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100)
    RATE_LIMIT_PER_HOUR: int = Field(default=1000)
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
