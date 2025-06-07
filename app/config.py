
import logging
import pathlib
from functools import lru_cache
from typing import Any, List, Optional

from pydantic import HttpUrl, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine the project root directory to reliably find the .env file
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

    # Project Meta
    PROJECT_NAME: str = "StatementSense"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database Configuration
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: str = "5432"
    DB_NAME: str
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Any:
        if isinstance(v, str):
            return v
            
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            username=values.get("DB_USER"),
            password=values.get("DB_PASS"),
            host=values.get("DB_HOST"),
            port=values.get("DB_PORT"),
            path=f"/{values.get('DB_NAME') or ''}",
            query="client_encoding=utf8"
        )
        
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: str = "50MB"  # Can be in bytes, KB, MB, GB, etc.
    ALLOWED_EXTENSIONS: str = "pdf"  # Comma-separated string
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MAX_FILE_SIZE string to bytes."""
        size_str = self.MAX_FILE_SIZE.upper().strip()
        if not size_str:
            return 0
            
        # Extract number and unit
        num = ""
        unit = ""
        for char in size_str:
            if char.isdigit() or char == '.':
                num += char
            else:
                unit = char
        
        if not num:
            return 0
            
        size = float(num)
        unit = unit.upper()
        
        # Convert to bytes
        if unit == 'B' or not unit:
            return int(size)
        elif unit == 'K':
            return int(size * 1024)
        elif unit == 'M':
            return int(size * 1024 * 1024)
        elif unit == 'G':
            return int(size * 1024 * 1024 * 1024)
        else:
            # Default to bytes if unknown unit
            return int(size)
    
    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get allowed extensions as a list."""
        return [
            ext.strip() 
            for ext in self.ALLOWED_EXTENSIONS.split(',')
            if ext.strip()
        ]
    
    # Ollama
    OLLAMA_URL: HttpUrl = "http://localhost:11434"
    
    # Logging
    LOG_LEVEL: str = "INFO"

    def get_logger(self, name: str) -> logging.Logger:
        """Configures and returns a logger instance."""
        logger = logging.getLogger(name)
        if not logger.handlers:  # Avoid adding multiple handlers
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(self.LOG_LEVEL.upper())
        return logger


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
