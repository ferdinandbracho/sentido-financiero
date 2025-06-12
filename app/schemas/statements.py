"""
Pydantic schemas for StatementSense application.

These schemas define the data structures for API requests/responses
and internal data validation for Mexican credit card statements.

Author: StatementSense
Created: June 2025
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class TransactionCategory(str, Enum):
    """Mexican transaction categories."""

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


class ExtractionMethod(str, Enum):
    """Extraction method used for parsing."""

    MEXICAN_TEMPLATE = "mexican_template"
    LLM_FALLBACK = "llm_fallback"
    HYBRID = "hybrid"
    TEXT_EXTRACTION_FAILED = "text_extraction_failed"


# Base Schemas
class CustomerInfo(BaseModel):
    """Customer information extracted from statement."""

    customer_name: Optional[str] = None
    card_number: Optional[str] = None
    bank_name: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentInfo(BaseModel):
    """Payment information from statement."""

    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    cut_date: Optional[datetime] = None
    due_date: Optional[str] = None  # Text format as in statement
    pay_no_interest: Optional[Decimal] = None
    minimum_payment: Optional[Decimal] = None
    confidence: float = Field(ge=0.0, le=1.0)

    class Config:
        from_attributes = True


class BalanceInfo(BaseModel):
    """Balance information from statement."""

    previous_balance: Optional[Decimal] = None
    total_charges: Optional[Decimal] = None
    total_payments: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    available_credit: Optional[Decimal] = None
    total_balance: Optional[Decimal] = None
    confidence: float = Field(ge=0.0, le=1.0)

    class Config:
        from_attributes = True


class Transaction(BaseModel):
    """Individual transaction record."""

    operation_date: datetime
    charge_date: Optional[datetime] = None
    description: str
    amount: Decimal
    transaction_type: TransactionType
    category: TransactionCategory = TransactionCategory.OTROS

    class Config:
        from_attributes = True
        use_enum_values = True


class ValidationResult(BaseModel):
    """Validation result for extracted data."""

    is_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    errors: List[str] = []
    warnings: List[str] = []

    class Config:
        from_attributes = True


class StatementExtractionData(BaseModel):
    """Complete extracted statement data."""

    customer_info: CustomerInfo
    payment_info: PaymentInfo
    balance_info: BalanceInfo
    transactions: List[Transaction]
    transactions_confidence: float = Field(ge=0.0, le=1.0)

    class Config:
        from_attributes = True


class StatementParsingResult(BaseModel):
    """Result of statement parsing operation."""

    success: bool
    data: Optional[StatementExtractionData] = None
    validation: Optional[ValidationResult] = None
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: ExtractionMethod
    error: Optional[str] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


# API Request/Response Schemas
class StatementUploadResponse(BaseModel):
    """Response for statement upload operation."""

    message: str
    statement_id: Optional[int] = None
    filename: str
    file_size: int
    processing_status: str
    extraction_result: Optional[StatementParsingResult] = None
    
    class Config:
        from_attributes = True


class StatementListResponse(BaseModel):
    """Response for listing statements."""

    statements: List[dict]  # Will be defined based on database model
    total_count: int
    page: int
    per_page: int
    
    class Config:
        from_attributes = True


class StatementDetailResponse(BaseModel):
    """Response for statement detail view."""

    statement_id: int
    filename: str
    upload_date: datetime
    bank_name: Optional[str]
    customer_name: Optional[str]
    statement_period: Optional[str]
    total_transactions: int
    total_amount: Optional[Decimal]
    extraction_method: ExtractionMethod
    confidence: float
    transactions: List[Transaction]
    
    class Config:
        from_attributes = True
        use_enum_values = True


class AnalysisRequest(BaseModel):
    """Request for statement analysis."""

    statement_id: int
    analysis_type: str = "summary"
    
    class Config:
        from_attributes = True  # summary, spending_patterns, categories


class SpendingAnalysis(BaseModel):
    """Spending analysis results."""

    total_spending: Decimal
    total_income: Decimal
    net_change: Decimal
    top_categories: List[dict]
    monthly_trend: List[dict]
    merchant_analysis: List[dict]
    
    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    """Response for analysis operations."""

    statement_id: int
    analysis_type: str
    generated_at: datetime
    spending_analysis: Optional[SpendingAnalysis] = None
    insights: List[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True


# Error Schemas
class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class ValidationError(BaseModel):
    """Validation error details."""

    field: str
    message: str
    invalid_value: Optional[str] = None
    
    class Config:
        from_attributes = True
