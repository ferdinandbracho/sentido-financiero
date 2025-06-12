from app.db.base import register_models
from app.models.statement import (
    ExtractionMethodEnum,
    LogLevelEnum,
    ProcessingStatusEnum,
    TransactionCategoryEnum,
    TransactionTypeEnum,
)

# This will register all SQLAlchemy models when the application starts
registered_models = register_models()

# Make models available at the package level
BankStatement = registered_models['BankStatement']
CategoryRule = registered_models['CategoryRule']
ProcessingLog = registered_models['ProcessingLog']
Transaction = registered_models['Transaction']

# Export models and enums
__all__ = [
    # Models
    'BankStatement',
    'CategoryRule',
    'ProcessingLog',
    'Transaction',
    
    # Enums
    'ProcessingStatusEnum',
    'ExtractionMethodEnum',
    'TransactionTypeEnum',
    'TransactionCategoryEnum',
    'LogLevelEnum',
]
