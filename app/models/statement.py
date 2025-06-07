from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgreUUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.db.base import Base


class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(PostgreUUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = Column(String(255), nullable=False)
    bank_name = Column(String(100), nullable=True)
    account_holder = Column(String(255), nullable=True)
    account_number = Column(String(50), nullable=True)
    statement_period_start = Column(DateTime, nullable=True)
    statement_period_end = Column(DateTime, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_status = Column(String(50), default="pending")  # pending, processed, failed
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    total_transactions = Column(Integer, default=0)
    total_credits = Column(Float, default=0.0)
    total_debits = Column(Float, default=0.0)
    raw_extracted_data = Column(Text, nullable=True)  # JSON string of raw extraction
    processing_notes = Column(Text, nullable=True)
    
    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BankStatement(id={self.id}, filename={self.filename}, status={self.processing_status})>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(PostgreUUID(as_uuid=True), primary_key=True, default=uuid4)
    statement_id = Column(PostgreUUID(as_uuid=True), ForeignKey("bank_statements.id"), nullable=False)
    
    # Transaction basic info
    transaction_date = Column(DateTime, nullable=False)
    processing_date = Column(DateTime, nullable=True)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # debit, credit
    
    # Categorization info
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)
    categorization_method = Column(String(50), nullable=True)  # exact_match, pattern_match, llm, manual
    
    # Additional analysis
    is_recurring = Column(Boolean, default=False)
    is_transfer = Column(Boolean, default=False)
    merchant_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Metadata
    raw_description = Column(String(500), nullable=True)  # Original uncleaned description
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back to statement
    statement = relationship("BankStatement", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.transaction_date}, amount={self.amount}, category={self.category})>"


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id = Column(PostgreUUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_name = Column(String(100), nullable=False, unique=True)
    rule_type = Column(String(50), nullable=False)  # exact_match, pattern_match, keyword
    pattern = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100), nullable=True)  # For future user management
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CategoryRule(id={self.id}, name={self.rule_name}, category={self.category})>"


class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id = Column(PostgreUUID(as_uuid=True), primary_key=True, default=uuid4)
    statement_id = Column(PostgreUUID(as_uuid=True), ForeignKey("bank_statements.id"), nullable=True)
    operation_type = Column(String(50), nullable=False)  # upload, extraction, categorization, analysis
    status = Column(String(50), nullable=False)  # started, completed, failed
    message = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    additional_data = Column(Text, nullable=True)  # JSON string for additional data (renamed from metadata)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to statement
    statement = relationship("BankStatement")
    
    def __repr__(self):
        return f"<ProcessingLog(id={self.id}, operation={self.operation_type}, status={self.status})>"
