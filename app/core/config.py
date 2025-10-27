from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    PROJECT_NAME: str = "Azure VNET Management API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Azure Configuration
    AZURE_SUBSCRIPTION_ID: str
    AZURE_TENANT_ID: str
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_RESOURCE_GROUP: str
    AZURE_LOCATION: str = "eastus"
    
    # Azure Table Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_STORAGE_TABLE_NAME: str = "vnetresources"
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Users 
    API_USERNAME: str = "admin"
    API_PASSWORD: str  
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()