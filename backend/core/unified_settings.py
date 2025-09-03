"""
Unified Settings System for AI Scholar
Centralizes all configuration management with proper validation and type safety.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseSettings, Field, validator
import os

class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(..., env="DATABASE_URL")
    pool_size: int = Field(20, env="DB_POOL_SIZE")
    max_overflow: int = Field(30, env="DB_MAX_OVERFLOW")
    pool_recycle: int = Field(3600, env="DB_POOL_RECYCLE")
    echo: bool = Field(False, env="DB_ECHO")
    
    class Config:
        env_prefix = "DB_"

class RedisSettings(BaseSettings):
    """Redis configuration"""
    url: str = Field(..., env="REDIS_URL")
    max_connections: int = Field(100, env="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(30, env="REDIS_SOCKET_TIMEOUT")
    decode_responses: bool = Field(True, env="REDIS_DECODE_RESPONSES")
    
    class Config:
        env_prefix = "REDIS_"

class AISettings(BaseSettings):
    """AI and ML configuration"""
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4-turbo-preview", env="OPENAI_MODEL")
    huggingface_api_key: Optional[str] = Field(None, env="HUGGINGFACE_API_KEY")
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    vector_dimension: int = Field(384, env="VECTOR_DIMENSION")
    
    class Config:
        env_prefix = "AI_"

class SecuritySettings(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
    bcrypt_rounds: int = Field(12, env="BCRYPT_ROUNDS")
    max_login_attempts: int = Field(5, env="MAX_LOGIN_ATTEMPTS")
    session_timeout_minutes: int = Field(60, env="SESSION_TIMEOUT_MINUTES")
    
    @validator('secret_key', 'jwt_secret_key')
    def validate_secret_keys(cls, v):
        if len(v) < 32:
            raise ValueError('Secret keys must be at least 32 characters long')
        return v
    
    class Config:
        env_prefix = "SECURITY_"

class FeatureFlags(BaseSettings):
    """Feature flag configuration"""
    enable_voice_processing: bool = Field(True, env="ENABLE_VOICE_PROCESSING")
    enable_jupyter_integration: bool = Field(True, env="ENABLE_JUPYTER_INTEGRATION")
    enable_zotero_integration: bool = Field(True, env="ENABLE_ZOTERO_INTEGRATION")
    enable_mobile_sync: bool = Field(True, env="ENABLE_MOBILE_SYNC")
    enable_analytics: bool = Field(True, env="ENABLE_ANALYTICS")
    enable_monitoring: bool = Field(True, env="ENABLE_MONITORING")
    enable_caching: bool = Field(True, env="ENABLE_CACHING")
    
    class Config:
        env_prefix = "FEATURE_"

class FileProcessingSettings(BaseSettings):
    """File processing configuration"""
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    supported_formats: List[str] = Field(
        ["pdf", "docx", "txt", "md", "rtf"], 
        env="SUPPORTED_FORMATS"
    )
    chunking_strategy: str = Field("hierarchical", env="CHUNKING_STRATEGY")
    chunk_size: int = Field(1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")
    ocr_engine: str = Field("tesseract", env="OCR_ENGINE")
    
    @validator('supported_formats', pre=True)
    def parse_supported_formats(cls, v):
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(',')]
        return v
    
    class Config:
        env_prefix = "FILE_"

class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration"""
    grafana_admin_password: Optional[str] = Field(None, env="GRAFANA_ADMIN_PASSWORD")
    prometheus_retention_days: int = Field(15, env="PROMETHEUS_RETENTION_DAYS")
    alert_email: Optional[str] = Field(None, env="ALERT_EMAIL")
    analytics_retention_days: int = Field(90, env="ANALYTICS_RETENTION_DAYS")
    enable_user_tracking: bool = Field(True, env="ENABLE_USER_TRACKING")
    privacy_mode: str = Field("strict", env="PRIVACY_MODE")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    @validator('privacy_mode')
    def validate_privacy_mode(cls, v):
        allowed = ['strict', 'moderate', 'minimal']
        if v not in allowed:
            raise ValueError(f'Privacy mode must be one of {allowed}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f'Log level must be one of {allowed}')
        return v.upper()
    
    class Config:
        env_prefix = "MONITORING_"

class PerformanceSettings(BaseSettings):
    """Performance configuration"""
    worker_processes: int = Field(4, env="WORKER_PROCESSES")
    max_concurrent_requests: int = Field(1000, env="MAX_CONCURRENT_REQUESTS")
    request_timeout_seconds: int = Field(30, env="REQUEST_TIMEOUT_SECONDS")
    cache_ttl_seconds: int = Field(3600, env="CACHE_TTL_SECONDS")
    max_memory_mb: int = Field(2048, env="MAX_MEMORY_MB")
    
    class Config:
        env_prefix = "PERFORMANCE_"

class UnifiedSettings(BaseSettings):
    """Main application settings"""
    
    # Core application settings
    app_name: str = Field("AI Scholar", env="APP_NAME")
    version: str = Field("2.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("production", env="ENVIRONMENT")
    
    # Component settings - these will be initialized with their own env vars
    database: DatabaseSettings = None
    redis: RedisSettings = None
    ai: AISettings = None
    security: SecuritySettings = None
    features: FeatureFlags = None
    file_processing: FileProcessingSettings = None
    monitoring: MonitoringSettings = None
    performance: PerformanceSettings = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize component settings
        self.database = DatabaseSettings()
        self.redis = RedisSettings()
        self.ai = AISettings()
        self.security = SecuritySettings()
        self.features = FeatureFlags()
        self.file_processing = FileProcessingSettings()
        self.monitoring = MonitoringSettings()
        self.performance = PerformanceSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed = ['development', 'staging', 'production', 'testing']
        if v not in allowed:
            raise ValueError(f'Environment must be one of {allowed}')
        return v
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == 'development' or self.debug
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == 'production' and not self.debug
    
    def get_database_url(self) -> str:
        """Get formatted database URL"""
        return self.database.url if self.database else ""
    
    def get_redis_url(self) -> str:
        """Get formatted Redis URL"""
        return self.redis.url if self.redis else ""
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.is_development():
            return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]
        else:
            # In production, these should come from environment variables
            origins = os.getenv("CORS_ORIGINS", "").split(",")
            return [origin.strip() for origin in origins if origin.strip()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive data)"""
        data = self.dict()
        
        # Remove sensitive information
        if 'security' in data and data['security']:
            data['security'] = {k: v for k, v in data['security'].items() 
                              if 'key' not in k.lower() and 'password' not in k.lower()}
        
        return data

@lru_cache()
def get_settings() -> UnifiedSettings:
    """Get cached settings instance"""
    return UnifiedSettings()

# Global settings instance
settings = get_settings()

# Export commonly used settings for backward compatibility
try:
    DATABASE_URL = settings.get_database_url()
    REDIS_URL = settings.get_redis_url()
    SECRET_KEY = settings.security.secret_key if settings.security else ""
    DEBUG = settings.debug
    ENVIRONMENT = settings.environment
    CORS_ORIGINS = settings.get_cors_origins()
except Exception as e:
    # Fallback for missing environment variables
    print(f"Warning: Settings initialization failed: {e}")
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    REDIS_URL = os.getenv("REDIS_URL", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    CORS_ORIGINS = ["http://localhost:3000"]

# Configuration validation
def validate_settings() -> Dict[str, Any]:
    """Validate all settings and return validation report"""
    validation_report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "settings_loaded": True
    }
    
    try:
        settings = get_settings()
        
        # Check required settings
        if not settings.get_database_url():
            validation_report["errors"].append("DATABASE_URL is required")
            validation_report["valid"] = False
        
        if not settings.get_redis_url():
            validation_report["warnings"].append("REDIS_URL not set - caching will be disabled")
        
        if settings.security and len(settings.security.secret_key) < 32:
            validation_report["errors"].append("SECRET_KEY must be at least 32 characters")
            validation_report["valid"] = False
        
        # Check AI settings
        if settings.ai and not settings.ai.openai_api_key and not settings.ai.huggingface_api_key:
            validation_report["warnings"].append("No AI API keys configured - AI features will be limited")
        
    except Exception as e:
        validation_report["valid"] = False
        validation_report["settings_loaded"] = False
        validation_report["errors"].append(f"Settings validation failed: {e}")
    
    return validation_report

if __name__ == "__main__":
    # Settings validation and reporting
    report = validate_settings()
    
    print("🔧 Settings Validation Report")
    print(f"Valid: {report['valid']}")
    print(f"Settings Loaded: {report['settings_loaded']}")
    
    if report['errors']:
        print("\n❌ Errors:")
        for error in report['errors']:
            print(f"  - {error}")
    
    if report['warnings']:
        print("\n⚠️  Warnings:")
        for warning in report['warnings']:
            print(f"  - {warning}")
    
    if report['valid']:
        print("\n✅ All settings are valid!")
        
        # Print configuration summary
        try:
            settings = get_settings()
            print(f"\n📋 Configuration Summary:")
            print(f"  App: {settings.app_name} v{settings.version}")
            print(f"  Environment: {settings.environment}")
            print(f"  Debug: {settings.debug}")
            print(f"  Database: {'✅ Configured' if settings.get_database_url() else '❌ Missing'}")
            print(f"  Redis: {'✅ Configured' if settings.get_redis_url() else '❌ Missing'}")
            print(f"  AI Services: {'✅ Configured' if settings.ai and settings.ai.openai_api_key else '⚠️  Limited'}")
        except Exception as e:
            print(f"  Error displaying summary: {e}")