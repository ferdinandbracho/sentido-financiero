import logging
import pathlib
from typing import Any, Optional

from pydantic import PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine the project root directory to reliably find the .env file
# This assumes config.py is in a subdirectory of the project root (e.g., app/config.py) # noqa: E501
# Adjust if your structure is different.
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,  # Load from .env file at project root
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields not defined in the model
    )

    PROJECT_NAME: str = "StatementSense"

    # OpenAI settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 150
    OPENAI_TEMPERATURE: float = 0.1

    # Upload settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Processing limits
    MAX_TRANSACTIONS_PER_STATEMENT: int = 1000
    PARSER_CACHE_SIZE: int = 1000
    MAX_PAGES_TO_PROCESS: int = 15  # Limit page processing for performance

    @field_validator("MAX_FILE_SIZE", mode="before")
    @classmethod
    def parse_max_file_size(cls, v: Any) -> int:
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            v = v.strip()
            # Handle '50MB' format
            if v.upper().endswith("MB"):
                return int(float(v[:-2].strip()) * 1024 * 1024)
            # Handle '50KB' format
            if v.upper().endswith("KB"):
                return int(float(v[:-2].strip()) * 1024)
            # Handle '50B' format
            if v.upper().endswith("B"):
                return int(float(v[:-1].strip()))
            # Try to convert to int directly
            return int(v)
        raise ValueError(
            f"MAX_FILE_SIZE must be an integer or a string with units (e.g., '50MB'), got {v}"
        )

    # Database Configuration
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: str = "5432"  # Default PostgreSQL port
    DB_NAME: str
    # DATABASE_URL will be assembled by the validator below
    # It's Optional here because it's constructed, not directly loaded
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Any:
        # If DATABASE_URL is explicitly set in .env, parse it
        if isinstance(v, str):
            # Ensure the URL has the correct scheme
            if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
                v = v.replace("postgres://", "postgresql://", 1)
                if not v.startswith("postgresql://"):
                    v = f"postgresql://{v}"
            return v

        # Otherwise, construct it from individual components
        values = info.data
        required_keys = ["DB_USER", "DB_PASS", "DB_HOST", "DB_PORT", "DB_NAME"]

        # Check if all required keys are present
        if not all(values.get(key) for key in required_keys):
            temp_logger = logging.getLogger(__name__)
            temp_logger.warning(
                "Critical database configuration variables are missing in .env. "
                "Cannot construct DATABASE_URL."
            )
            return None

        # Get and clean the database name
        db_name = (values.get("DB_NAME") or "").strip().lstrip("/")
        if not db_name:
            raise ValueError("Database name (DB_NAME) is required in .env")

        # Build the URL components
        user = values.get("DB_USER", "").strip()
        password = values.get("DB_PASS", "").strip()
        host = values.get("DB_HOST", "localhost").strip()
        port = str(values.get("DB_PORT", "5432")).strip()

        # Construct the URL using string formatting for better control
        auth_part = f"{user}:{password}@" if user and password else ""
        port_part = f":{port}" if port else ""
        path_part = f"/{db_name}"

        db_url = (
            f"postgresql+psycopg2://{auth_part}{host}{port_part}{path_part}"
        )

        # Validate the constructed URL
        try:
            return PostgresDsn(db_url)
        except ValueError as e:
            raise ValueError(f"Invalid database URL format: {e}") from e

    # Example Configuration (optional fields)
    EXAMPLE_URL: Optional[str] = None
    EXAMPLE_QUEUE_USERS: Optional[str] = None
    EXAMPLE_ERROR: Optional[str] = None

    # CORS Configuration
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> str:
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return v
        return ",".join(v) if isinstance(v, list) else str(v)
    
    def get_cors_origins(self) -> list[str]:
        """Get CORS origins as a list."""
        if not self.BACKEND_CORS_ORIGINS:
            return ["*"]  # Fallback to allow all origins
        
        # Handle the case where it might be parsed as a JSON string
        origins_str = self.BACKEND_CORS_ORIGINS
        if origins_str.startswith('[') and origins_str.endswith(']'):
            # Try to parse as JSON-like string
            import json
            try:
                return json.loads(origins_str)
            except json.JSONDecodeError:
                pass
        
        # Split by comma and clean up
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    
    # File Upload Configuration
    ALLOWED_EXTENSIONS: str = "pdf"
    
    def get_allowed_extensions(self) -> list[str]:
        """Get allowed file extensions as a list."""
        if not self.ALLOWED_EXTENSIONS:
            return [".pdf"]
        extensions = [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
        # Ensure extensions start with a dot
        return [ext if ext.startswith(".") else f".{ext}" for ext in extensions]
    
    # Environment Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"

    def get_logger(self, name: str) -> logging.Logger:
        """Configures and returns a logger instance."""
        logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        if (
            not logger.handlers
        ):  # Avoid adding multiple handlers if called multiple times
            logger.addHandler(handler)
        logger.setLevel(self.LOG_LEVEL.upper())

        # File logging can be enabled in production environments if needed
        # Example: Add file handler for persistent logging
        # file_handler = logging.FileHandler(PROJECT_ROOT / "app.log")
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

        return logger


# Create a single instance of the settings to be used throughout the application
settings = Settings()

# Usage example:
# from app.config import settings
# logger = settings.get_logger(__name__)
# logger.info("Module loaded successfully")
