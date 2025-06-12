"""
Statement processing API endpoints.

Handles file uploads, processing, and retrieval of Mexican credit card
statements using template-based parsing with LLM fallback.

Author: Ferdinand Bracho
Created: June 2025
"""

# Standard library imports
from decimal import Decimal
from typing import Optional

# Third-party imports
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

# Local application imports
from app.config import settings
from app.db.session import get_db
from app.models.statement import (
    BankStatement,
    LogLevelEnum,
    ProcessingLog,
    Transaction,
    TransactionCategoryEnum,
    TransactionTypeEnum,
    ProcessingStatusEnum,
    ExtractionMethodEnum,
)
from app.schemas.statements import (
    ErrorResponse,
    ExtractionMethod,
    StatementDetailResponse,
    StatementListResponse,
    StatementUploadResponse,
    TransactionType,
)
from app.services.pdf_parser import pdf_processor

logger = settings.get_logger(__name__)
router = APIRouter()

# File upload constraints
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.get(
    "/",
    response_model=StatementListResponse,
    responses={
        200: {"model": StatementListResponse},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="List all statements",
    description="Retrieve a paginated list of all processed statements",
)
async def root(
    page: int = 1,
    per_page: int = 20,
    bank_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Root endpoint that lists all statements."""
    return await list_statements(
        page=page, per_page=per_page, bank_name=bank_name, db=db
    )


ALLOWED_EXTENSIONS = {".pdf"}


def validate_upload_file(file: UploadFile) -> None:
    """Validate uploaded file constraints."""

    # Check file extension
    if not file.filename or not any(
        file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Note: file.size is not always available, so we'll check size during processing


@router.post(
    "/upload",
    response_model=StatementUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process credit card statement",
    description="Upload a PDF credit card statement for processing and analysis",
)
async def upload_statement(
    file: UploadFile = File(..., description="PDF statement file"),
    db: Session = Depends(get_db),
) -> StatementUploadResponse:
    """
    Upload and process a credit card statement PDF.

    - **file**: PDF file containing credit card statement
    - Returns processing results and extracted data
    """

    try:
        # Validate file
        validate_upload_file(file)

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB",
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded",
            )

        logger.info(
            f"Processing uploaded file: {file.filename} ({file_size} bytes)"
        )

        # Validate PDF format
        if not pdf_processor.validate_pdf(file_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or corrupted PDF file",
            )

        # Process statement using template-first approach
        extraction_result = pdf_processor.process_statement(file_content)
        
        # Log the extraction result (without sensitive data)
        result_log = {
            'success': extraction_result.get('success'),
            'confidence': extraction_result.get('confidence'),
            'extraction_method': extraction_result.get('extraction_method'),
            'error': extraction_result.get('error'),
            'has_raw_text': bool(extraction_result.get('raw_text'))
        }
        logger.info(f"Statement processing result: {result_log}")

        # Ensure we have raw text
        raw_text = extraction_result.get('raw_text', '')
        if not raw_text and extraction_result.get('success', False):
            logger.warning("No raw text in successful extraction result")
            raw_text = "[No text extracted]"

        # Save to database
        db_statement = BankStatement(
            filename=file.filename,
            file_size=file_size,
            raw_text=raw_text,
            processing_status=(
                ProcessingStatusEnum.COMPLETED 
                if extraction_result.get("success", False)
                else ProcessingStatusEnum.FAILED
            ),
            extraction_method=(
                ExtractionMethodEnum.MEXICAN_TEMPLATE 
                if extraction_result.get("method") == "template" 
                else ExtractionMethodEnum.LLM_FALLBACK
            ),
            overall_confidence=extraction_result.get("confidence"),
        )

        # Add extracted metadata if available
        if extraction_result.get("success") and "metadata" in extraction_result:
            meta = extraction_result["metadata"]
            db_statement.bank_name = meta.get("bank_name")
            db_statement.customer_name = meta.get("customer_name")
            db_statement.card_number_last4 = meta.get("card_last_four")
            db_statement.statement_period_start = meta.get("period_start")
            db_statement.statement_period_end = meta.get("period_end")
            db_statement.cut_date = meta.get("cut_date")
            db_statement.due_date = meta.get("due_date")
            db_statement.previous_balance = meta.get("previous_balance")
            db_statement.total_charges = meta.get("total_charges")
            db_statement.total_payments = meta.get("total_payments")
            db_statement.credit_limit = meta.get("credit_limit")
            db_statement.available_credit = meta.get("available_credit")
            db_statement.total_balance = meta.get("total_balance")

            # Add transactions if available
            if "transactions" in extraction_result:
                for tx_data in extraction_result["transactions"]:
                    transaction = Transaction(
                        operation_date=tx_data.get("date"),
                        charge_date=tx_data.get("charge_date"),
                        description=tx_data.get("description", ""),
                        amount=tx_data.get("amount"),
                        transaction_type=(
                            TransactionTypeEnum.CARGO 
                            if tx_data.get("type") == "DEBIT" 
                            else TransactionTypeEnum.ABONO
                        ),
                        category=tx_data.get("category", TransactionCategoryEnum.OTROS),
                        original_category=tx_data.get("original_category"),
                        categorization_confidence=tx_data.get("confidence"),
                    )
                    db_statement.transactions.append(transaction)

        # Add processing log
        log = ProcessingLog(
            level=LogLevelEnum.INFO if extraction_result["success"] else LogLevelEnum.ERROR,
            message=(
                "Successfully processed statement" 
                if extraction_result["success"] 
                else "Failed to process statement"
            ),
            details={
                "filename": file.filename,
                "method": extraction_result.get("extraction_method"),
                "error": extraction_result.get("error"),
            },
        )
        db_statement.processing_logs.append(log)

        # Save to database
        db.add(db_statement)
        db.commit()
        db.refresh(db_statement)

        response = StatementUploadResponse(
            message=(
                "Statement uploaded and processed successfully"
                if extraction_result["success"]
                else "Statement processed with some errors"
            ),
            statement_id=db_statement.id,
            filename=file.filename,
            file_size=file_size,
            processing_status=(
                "completed" if extraction_result["success"] else "failed"
            ),
            extraction_result=extraction_result,
        )

        logger.info(f"Successfully processed statement: {file.filename}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing file: {str(e)}",
        )


@router.get(
    "/",
    response_model=StatementListResponse,
    summary="List uploaded statements",
    description="Retrieve a list of uploaded statements with pagination",
)
async def list_statements(
    page: int = 1,
    per_page: int = 20,
    bank_name: Optional[str] = None,
    db: Session = Depends(get_db),
) -> StatementListResponse:
    """
    List uploaded statements with optional filtering.

    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **bank_name**: Filter by bank name (optional)
    """

    try:
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1",
            )

        if per_page < 1 or per_page > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Per page must be between 1 and 100",
            )

        # Paginate results
        offset = (page - 1) * per_page
        query = db.query(BankStatement)
        if bank_name:
            query = query.filter(
                BankStatement.bank_name.ilike(f"%{bank_name}%")
            )
        total = query.count()
        statements = query.offset(offset).limit(per_page).all()

        # Convert statements to response models
        statement_responses = []
        for statement in statements:
            # Calculate total amount from transactions if available
            total_amount = None
            total_transactions = 0
            if hasattr(statement, 'transactions') and statement.transactions:
                total_amount = sum(
                    float(tx.amount) for tx in statement.transactions
                    if tx.amount is not None
                )
                total_transactions = len(statement.transactions)
            
            # Format statement period if available
            statement_period = None
            if (
                statement.statement_period_start and
                statement.statement_period_end
            ):
                start = statement.statement_period_start.strftime('%Y-%m-%d')
                end = statement.statement_period_end.strftime('%Y-%m-%d')
                statement_period = f"{start} to {end}"
            
            # Map transaction types from database to schema
            mapped_transactions = []
            for tx in statement.transactions or []:
                # Create a copy of the transaction
                tx_dict = {
                    "operation_date": tx.operation_date,
                    "charge_date": tx.charge_date,
                    "description": tx.description,
                    "amount": tx.amount,
                    "category": tx.category,
                    # Map transaction type from database to schema
                    "transaction_type": TransactionType.DEBIT if tx.transaction_type == TransactionTypeEnum.CARGO else TransactionType.CREDIT
                }
                mapped_transactions.append(tx_dict)
                
            # Create response model
            response = StatementDetailResponse(
                statement_id=statement.id,
                filename=statement.filename,
                upload_date=statement.upload_date,
                bank_name=statement.bank_name,
                customer_name=statement.customer_name,
                statement_period=statement_period,
                total_transactions=total_transactions,
                total_amount=(
                    Decimal(str(total_amount)) 
                    if total_amount is not None else None
                ),
                extraction_method=(
                    statement.extraction_method or 
                    ExtractionMethod.MEXICAN_TEMPLATE
                ),
                confidence=statement.overall_confidence or 0.0,
                transactions=mapped_transactions
            )
            statement_responses.append(response)
        
        # Convert statements to dictionaries
        statements_list = []
        for stmt in statements:
            # Calculate total amount and count from transactions
            stmt_total_transactions = (
                len(stmt.transactions) if stmt.transactions else 0
            )
            stmt_total_amount = (
                sum(
                    float(tx.amount) 
                    for tx in (stmt.transactions or []) 
                    if tx.amount is not None
                ) if stmt.transactions else 0.0
            )

            # Format statement period if available
            stmt_period = None
            if stmt.statement_period_start and stmt.statement_period_end:
                start = stmt.statement_period_start.strftime('%Y-%m-%d')
                end = stmt.statement_period_end.strftime('%Y-%m-%d')
                stmt_period = f"{start} to {end}"

            # Map transactions to dictionaries
            transactions_list = []
            for tx in stmt.transactions or []:
                tx_dict = {
                    "operation_date": tx.operation_date,
                    "charge_date": tx.charge_date,
                    "description": tx.description or "",
                    "amount": (
                        float(tx.amount) 
                        if tx.amount is not None 
                        else 0.0
                    ),
                    "transaction_type": (
                        TransactionType.DEBIT 
                        if tx.transaction_type == TransactionTypeEnum.CARGO 
                        else TransactionType.CREDIT
                    ),
                    "category": tx.category or TransactionCategoryEnum.OTROS,
                    "original_category": tx.original_category,
                    "categorization_confidence": tx.categorization_confidence
                }
                transactions_list.append(tx_dict)

            stmt_dict = {
                'statement_id': stmt.id,
                'filename': stmt.filename,
                'upload_date': stmt.upload_date,
                'bank_name': stmt.bank_name,
                'customer_name': stmt.customer_name or "",
                'statement_period': stmt_period,
                'total_transactions': stmt_total_transactions,
                'total_amount': stmt_total_amount,
                'extraction_method': (
                    stmt.extraction_method or "MEXICAN_TEMPLATE"
                ),
                'confidence': float(stmt.overall_confidence or 0.0),
                'transactions': transactions_list
            }
            statements_list.append(stmt_dict)
        
        # Create and return the response
        return StatementListResponse(
            statements=statements_list,
            total_count=total,
            page=page,
            per_page=per_page
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing statements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error retrieving statements",
        )


@router.get(
    "/{statement_id}",
    response_model=StatementDetailResponse,
    summary="Get statement details",
    description="Retrieve detailed information about a specific statement",
)
async def get_statement_detail(
    statement_id: int, db: Session = Depends(get_db)
) -> StatementDetailResponse:
    """
    Get detailed information about a specific statement.

    - **statement_id**: ID of the statement to retrieve
    """

    try:
        # TODO: Implement database query once models are ready
        # For now, return not found

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement with ID {statement_id} not found",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving statement {statement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error retrieving statement",
        )


@router.delete(
    "/{statement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete statement",
    description="Delete a statement and all associated data",
)
async def delete_statement(statement_id: int, db: Session = Depends(get_db)):
    """
    Delete a statement and all associated data.

    - **statement_id**: ID of the statement to delete
    """

    try:
        # TODO: Implement database deletion once models are ready
        # For now, return not found

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement with ID {statement_id} not found",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting statement {statement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error deleting statement",
        )


@router.post(
    "/test-parsing",
    summary="Test statement parsing",
    description="Test the Mexican template parser with a PDF file (development endpoint)",
)
async def test_parsing(
    file: UploadFile = File(..., description="PDF statement file for testing"),
):
    """
    Development endpoint to test the Mexican template parser.
    Returns detailed parsing results for debugging.
    """

    try:
        validate_upload_file(file)

        file_content = await file.read()

        if not pdf_processor.validate_pdf(file_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file",
            )

        # Get detailed parsing results
        result = pdf_processor.process_statement(file_content)

        # Add PDF metadata for debugging
        pdf_metadata = pdf_processor.get_pdf_metadata(file_content)

        return {
            "filename": file.filename,
            "file_size": len(file_content),
            "pdf_metadata": pdf_metadata,
            "parsing_result": result,
            "debug_info": {
                "extraction_method": result.get("extraction_method"),
                "confidence": result.get("confidence"),
                "validation": result.get("validation", {}),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in test parsing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )
