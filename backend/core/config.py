"""
Configuration settings for the application
"""
import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "AI Scholar RAG Backend"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Database
    DATABASE_URL: str = "sqlite:///./ai_scholar.db"
    
    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # Vector Store
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_EXPIRE_TIME: int = 3600  # 1 hour default
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OAuth 2.0 Settings
    OAUTH_JWT_SECRET: str = "your-oauth-jwt-secret-change-in-production"
    OAUTH_ACCESS_TOKEN_EXPIRE_HOURS: int = 1
    OAUTH_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    OAUTH_AUTH_CODE_EXPIRE_MINUTES: int = 10
    
    # Integration Authentication
    API_KEY_DEFAULT_RATE_LIMIT: int = 1000
    API_KEY_MAX_RATE_LIMIT: int = 10000
    INTEGRATION_AUTH_ENABLED: bool = True
    
    # Base URL for OAuth redirects
    BASE_URL: str = "http://localhost:8000"
    
    # Zotero Integration Settings
    ZOTERO_CLIENT_ID: str = "your-zotero-client-id"
    ZOTERO_CLIENT_SECRET: str = "your-zotero-client-secret"
    ZOTERO_REDIRECT_URI: str = "http://localhost:8000/api/zotero/oauth/callback"
    ZOTERO_API_BASE_URL: str = "https://api.zotero.org"
    ZOTERO_OAUTH_BASE_URL: str = "https://www.zotero.org/oauth"
    ZOTERO_DEFAULT_SYNC_FREQUENCY: int = 60  # minutes
    ZOTERO_MAX_ATTACHMENT_SIZE_MB: int = 50
    ZOTERO_ATTACHMENTS_DIR: str = "./zotero_attachments"
    
    # Attachment Storage Settings
    ATTACHMENT_STORAGE_PATH: str = "./zotero_attachments"
    MAX_ATTACHMENT_SIZE_MB: int = 50
    
    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "./uploads"
    
    # Processing
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from environment

settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings

# File Upload Security Configuration
ALLOWED_FILE_TYPES = [
    'application/pdf',
    'text/plain', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword'
]

# File size limits (in MB)
MAX_FILE_SIZE_MB = 50
MAX_BATCH_FILES = 10
MAX_TOTAL_BATCH_SIZE_MB = 200

# Security settings
ENABLE_MAGIC_BYTE_VALIDATION = True
ENABLE_VIRUS_SCANNING = False  # Set to True in production with ClamAV
ENABLE_FILE_QUARANTINE = True
QUARANTINE_DIRECTORY = "quarantine"

# Upload paths
UPLOAD_DIRECTORY = "uploads"
TEMP_DIRECTORY = "temp"
PROCESSED_DIRECTORY = "processed"

# Rate limiting
MAX_UPLOADS_PER_HOUR = 100
MAX_UPLOADS_PER_DAY = 500

# Authentication settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
REFRESH_TOKEN_EXPIRATION_DAYS = 30

# Session security
SESSION_TIMEOUT_MINUTES = 60
MAX_CONCURRENT_SESSIONS = 5
ENABLE_SESSION_MONITORING = True
