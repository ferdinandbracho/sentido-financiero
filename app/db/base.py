from sqlalchemy.ext.declarative import declarative_base

# Base for SQLAlchemy models
Base = declarative_base()

# This will be called after all models are defined
def register_models():
    # Import models here to avoid circular imports
    from app.models.statement import (
        BankStatement,
        CategoryRule,
        ProcessingLog,
        Transaction,
    )
    # This ensures that SQLAlchemy knows about all models
    return {
        'BankStatement': BankStatement,
        'CategoryRule': CategoryRule,
        'ProcessingLog': ProcessingLog,
        'Transaction': Transaction,
    }
