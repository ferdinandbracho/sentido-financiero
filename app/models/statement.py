import enum

from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# Using enums from schemas directly for consistency if possible,
# or redefining them here for SQLAlchemy Enum type.
# For simplicity, we'll use string representations for now,
# but SQLAlchemy's Enum type is preferred for stricter validation.

class TransactionTypeEnum(str, enum.Enum):
    CARGO = "cargo"  # Charge
    ABONO = "abono"  # Payment/Credit


class TransactionCategoryEnum(str, enum.Enum):
    ALIMENTACION = "alimentacion"
    GASOLINERAS = "gasolineras"
    SALUD = "salud"
    TRANSPORTE = "transporte"
    ENTRETENIMIENTO = "entretenimiento"
    ROPA = "ropa"
    SERVICIOS = "servicios"
    EDUCACION = "educacion"
    SEGUROS = "seguros"
    TRANSFERENCIAS = "transferencias"
    INTERESES_COMISIONES = "intereses_comisiones"
    OTROS = "otros"


class ExtractionMethodEnum(str, enum.Enum):
    MEXICAN_TEMPLATE = "mexican_template"
    LLM_FALLBACK = "llm_fallback"
    HYBRID = "hybrid"
    TEXT_EXTRACTION_FAILED = "text_extraction_failed"


class ProcessingStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class LogLevelEnum(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True, comment="File size in bytes")
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    
    bank_name = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)
    # Assuming storing last 4 digits
    card_number_last4 = Column(String(4), nullable=True)

    statement_period_start = Column(DateTime, nullable=True)
    statement_period_end = Column(DateTime, nullable=True)
    cut_date = Column(DateTime, nullable=True)
    due_date = Column(String, nullable=True) # Kept as string as per schema

    pay_no_interest = Column(DECIMAL(precision=10, scale=2), nullable=True)
    minimum_payment = Column(DECIMAL(precision=10, scale=2), nullable=True)
    
    previous_balance = Column(DECIMAL(precision=10, scale=2), nullable=True)
    total_charges = Column(DECIMAL(precision=10, scale=2), nullable=True)
    total_payments = Column(DECIMAL(precision=10, scale=2), nullable=True)
    credit_limit = Column(DECIMAL(precision=10, scale=2), nullable=True)
    available_credit = Column(DECIMAL(precision=10, scale=2), nullable=True)
    # From BankStatementRead
    total_balance = Column(
        DECIMAL(precision=10, scale=2), nullable=True
    )

    extraction_method = Column(Enum(ExtractionMethodEnum), nullable=True)
    # Renamed from 'confidence' to avoid clash
    overall_confidence = Column(Float, nullable=True)
    processing_status = Column(Enum(ProcessingStatusEnum), default=ProcessingStatusEnum.PENDING)
    raw_text = Column(Text, nullable=True)
    
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    transactions = relationship(
        "Transaction",
        back_populates="statement",
        cascade="all, delete-orphan",
    )
    processing_logs = relationship(
        "ProcessingLog",
        back_populates="statement",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<BankStatement(id={self.id}, filename='{self.filename}')>"
        )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(
        Integer, ForeignKey("bank_statements.id"), nullable=False
    )
    
    operation_date = Column(DateTime, nullable=False)
    # From TransactionRead, optional
    charge_date = Column(DateTime, nullable=True)
    description = Column(String, nullable=False)
    amount = Column(DECIMAL(precision=10, scale=2), nullable=False)
    
    transaction_type = Column(Enum(TransactionTypeEnum), nullable=False)
    category = Column(Enum(TransactionCategoryEnum), default=TransactionCategoryEnum.OTROS)
    # If user overrides the automatically assigned category
    original_category = Column(Enum(TransactionCategoryEnum), nullable=True)
    categorization_confidence = Column(Float, nullable=True)
    is_manual_edit = Column(Boolean, default=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    statement = relationship(
        "BankStatement", back_populates="transactions"
    )

    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, "
            f"description='{self.description[:20]}...', amount={self.amount})>"
        )


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id = Column(Integer, primary_key=True, index=True)
    # Keyword for exact matching rules
    keyword = Column(String, index=True, nullable=False, unique=True)
    pattern = Column(String, nullable=True, unique=True)  # Regex pattern
    category = Column(
        Enum(TransactionCategoryEnum), nullable=False
    )
    priority = Column(Integer, default=2)  # Tier 1 (exact), Tier 2 (pattern)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    def __repr__(self):
        return (
            f"<CategoryRule(id={self.id}, keyword='{self.keyword}', "
            f"category='{self.category.value}')>"
        )


class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(
        Integer, ForeignKey("bank_statements.id"), nullable=False
    )
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    level = Column(Enum(LogLevelEnum), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # For structured error info

    statement = relationship(
        "BankStatement", back_populates="processing_logs"
    )

    def __repr__(self):
        return (
            f"<ProcessingLog(id={self.id}, level='{self.level.value}', "
            f"message='{self.message[:30]}...')>"
        )
