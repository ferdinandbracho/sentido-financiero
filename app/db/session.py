import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL and log it (without password for security)
db_url = str(settings.DATABASE_URL)
logger.info("Connecting to database: %s", db_url.split('@')[-1])

# Create engine with additional configuration
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=True,  # Enable SQL query logging
    json_serializer=str,  # Ensure proper JSON serialization
    connect_args={
        'connect_timeout': 10,  # 10 second timeout
        'options': '-c client_encoding=utf8',  # Ensure UTF-8 encoding
        'client_encoding': 'utf8',  # Set client encoding
    }
)

# Ensure proper Unicode handling
engine.dialect.encoding = 'utf-8'

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base from base.py (not defined here)
from app.db.base import Base  # noqa

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
