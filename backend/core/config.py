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
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
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
    
    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "./uploads"
    
    # Processing
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    
    class Config:
        env_file = ".env"

settings = Settings()