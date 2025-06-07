# Need to import here all models
from sqlalchemy.ext.declarative import declarative_base

# Base for SQLAlchemy models
Base = declarative_base()

# Import all models here to ensure they are registered with Base
from app.models.statement import (  # noqa
    BankStatement,
    Transaction, 
    CategoryRule,
    ProcessingLog
)