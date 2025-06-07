from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Base Transaction Schema
class TransactionBase(BaseModel):
    transaction_date: datetime
    processing_date: Optional[datetime] = None
    description: str
    amount: float
    transaction_type: str = Field(..., description="debit or credit")
    category: Optional[str] = None
    subcategory: Optional[str] = None
    confidence_score: Optional[float] = None
    categorization_method: Optional[str] = None
    is_recurring: bool = False
    is_transfer: bool = False
    merchant_name: Optional[str] = None
    location: Optional[str] = None
    raw_description: Optional[str] = None
    notes: Optional[str] = None


class TransactionCreate(TransactionBase):
    statement_id: UUID


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    notes: Optional[str] = None
    is_recurring: Optional[bool] = None
    is_transfer: Optional[bool] = None


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    statement_id: UUID
    created_at: datetime
    updated_at: datetime


# Base BankStatement Schema
class BankStatementBase(BaseModel):
    filename: str
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    account_number: Optional[str] = None
    statement_period_start: Optional[datetime] = None
    statement_period_end: Optional[datetime] = None
    processing_status: str = "pending"
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    processing_notes: Optional[str] = None


class BankStatementCreate(BankStatementBase):
    pass


class BankStatementUpdate(BaseModel):
    processing_status: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    account_number: Optional[str] = None
    statement_period_start: Optional[datetime] = None
    statement_period_end: Optional[datetime] = None
    total_transactions: Optional[int] = None
    total_credits: Optional[float] = None
    total_debits: Optional[float] = None
    processing_notes: Optional[str] = None


class BankStatementResponse(BankStatementBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    upload_date: datetime
    total_transactions: int
    total_credits: float
    total_debits: float
    transactions: List[TransactionResponse] = []


class BankStatementSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    bank_name: Optional[str]
    account_holder: Optional[str]
    processing_status: str
    upload_date: datetime
    statement_period_start: Optional[datetime]
    statement_period_end: Optional[datetime]
    total_transactions: int
    total_credits: float
    total_debits: float


# Category Rule Schemas
class CategoryRuleBase(BaseModel):
    rule_name: str
    rule_type: str = Field(..., description="exact_match, pattern_match, or keyword")
    pattern: str
    category: str
    subcategory: Optional[str] = None
    priority: int = 0
    is_active: bool = True


class CategoryRuleCreate(CategoryRuleBase):
    created_by: Optional[str] = None


class CategoryRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    pattern: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryRuleResponse(CategoryRuleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime


# Processing Log Schemas
class ProcessingLogBase(BaseModel):
    operation_type: str = Field(..., description="upload, extraction, categorization, analysis")
    status: str = Field(..., description="started, completed, failed")
    message: Optional[str] = None
    error_details: Optional[str] = None
    duration_seconds: Optional[float] = None
    additional_data: Optional[str] = None  # Renamed from metadata


class ProcessingLogCreate(ProcessingLogBase):
    statement_id: Optional[UUID] = None


class ProcessingLogResponse(ProcessingLogBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    statement_id: Optional[UUID]
    timestamp: datetime


# Analysis & Report Schemas
class CategorySummary(BaseModel):
    category: str
    subcategory: Optional[str]
    transaction_count: int
    total_amount: float
    average_amount: float
    percentage_of_total: float


class MonthlySpendingSummary(BaseModel):
    month_year: str
    total_spent: float
    total_income: float
    net_amount: float
    transaction_count: int
    top_categories: List[CategorySummary]


class SpendingAnalysis(BaseModel):
    statement_id: UUID
    analysis_period: str
    total_transactions: int
    total_credits: float
    total_debits: float
    net_amount: float
    categories: List[CategorySummary]
    monthly_breakdown: List[MonthlySpendingSummary]
    recurring_transactions: List[TransactionResponse]
    largest_expenses: List[TransactionResponse]
    categorization_stats: dict


# File Upload Response
class FileUploadResponse(BaseModel):
    statement_id: UUID
    filename: str
    file_size: int
    status: str
    message: str


# Processing Status Response
class ProcessingStatusResponse(BaseModel):
    statement_id: UUID
    status: str
    progress_percentage: Optional[float] = None
    current_operation: Optional[str] = None
    message: Optional[str] = None
    error_details: Optional[str] = None
    estimated_completion: Optional[datetime] = None


# Categorization Stats
class CategorizationStats(BaseModel):
    total_transactions: int
    exact_matches: int
    pattern_matches: int
    llm_categorizations: int
    manual_categorizations: int
    uncategorized: int
    average_confidence: float
    processing_time_seconds: float
