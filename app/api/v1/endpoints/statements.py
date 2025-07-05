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
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

# Local application imports
from app.config import settings
from app.db.session import get_db
from app.models.statement import (
    BankStatement,
    ExtractionMethodEnum,
    LogLevelEnum,
    ProcessingLog,
    ProcessingStatusEnum,
    Transaction,
    TransactionCategoryEnum,
    TransactionTypeEnum,
)
from app.schemas.statements import (
    BulkDeleteRequest,
    BulkDownloadRequest,
    BulkOperationResponse,
    ErrorResponse,
    ExtractionMethod,
    StatementDetailResponse,
    StatementListResponse,
    StatementUploadResponse,
    TransactionType,
)
from sqlalchemy import func
from app.services.pdf_parser import pdf_processor

logger = settings.get_logger(__name__)
router = APIRouter()

# File upload constraints
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Month names in Spanish
MONTH_NAMES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

def generate_formatted_filename(bank_name: str, statement_period_start) -> str:
    """
    Generate a formatted filename based on bank name and statement period.
    Format: "Bank - Month Year" (e.g., "BBVA - Abril 2025")
    """
    if not bank_name or not statement_period_start:
        return None
    
    # Extract month and year from statement_period_start
    month = statement_period_start.month
    year = statement_period_start.year
    
    # Format: "BANK - Month Year"
    month_name = MONTH_NAMES.get(month, "Desconocido")
    return f"{bank_name.upper()} - {month_name} {year}"

def check_duplicate_statement(db: Session, bank_name: str, statement_period_start) -> Optional[BankStatement]:
    """
    Check if a statement with the same bank and period already exists.
    Returns the existing statement if found, None otherwise.
    """
    if not bank_name or not statement_period_start:
        return None
    
    # Check for existing statement with same bank and period start
    existing_statement = db.query(BankStatement).filter(
        func.lower(BankStatement.bank_name) == func.lower(bank_name),
        func.date(BankStatement.statement_period_start) == func.date(statement_period_start)
    ).first()
    
    return existing_statement


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
            detail=(
                f"File type not supported. Allowed extensions: "
                f"{', '.join(ALLOWED_EXTENSIONS)}"
            ),
        )

    # Note: file.size is not always available, so we'll check size during
    # processing


@router.post(
    "/upload",
    response_model=StatementUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process credit card statement",
    description=(
        "Upload a PDF credit card statement for processing and analysis"
    ),
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
                detail=(
                    f"File too large. Maximum size: "
                    f"{MAX_FILE_SIZE // (1024 * 1024)}MB"
                ),
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
        extraction_result = pdf_processor.process_statement(file_content, file.filename)

        # Log the extraction result (without sensitive data)
        result_log = {
            "success": extraction_result.get("success"),
            "confidence": extraction_result.get("confidence"),
            "extraction_method": extraction_result.get("extraction_method"),
            "error": extraction_result.get("error"),
            "has_raw_text": bool(extraction_result.get("raw_text")),
        }
        logger.info(f"Statement processing result: {result_log}")

        # Ensure we have raw text
        raw_text = extraction_result.get("raw_text", "")
        if not raw_text and extraction_result.get("success", False):
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
                if extraction_result.get("extraction_method") in ["ocr_table_parser", "enhanced_table_extraction"]
                else ExtractionMethodEnum.LLM_FALLBACK
                if extraction_result.get("extraction_method") == "llm_fallback"
                else ExtractionMethodEnum.MEXICAN_TEMPLATE
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
            
            # Check for duplicate statement
            bank_name = meta.get("bank_name")
            period_start = meta.get("period_start")
            
            if bank_name and period_start:
                existing_statement = check_duplicate_statement(db, bank_name, period_start)
                if existing_statement:
                    # Generate formatted name for the error message
                    formatted_name = generate_formatted_filename(bank_name, period_start)
                    fallback_name = f"{bank_name} - {period_start.strftime('%B %Y')}"
                    display_name = formatted_name or fallback_name
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "error": "duplicate_statement",
                            "message": f"Ya existe un estado de cuenta para {display_name}",
                            "existing_statement_id": existing_statement.id,
                            "formatted_name": formatted_name
                        }
                    )
                
                # Auto-rename the file with the formatted name
                formatted_filename = generate_formatted_filename(bank_name, period_start)
                if formatted_filename:
                    db_statement.filename = formatted_filename
                    logger.info(f"Auto-renamed statement to: {formatted_filename}")

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
                            if tx_data.get("type") in ["cargo", "DEBIT"]
                            else TransactionTypeEnum.ABONO
                        ),
                        category=tx_data.get(
                            "category", TransactionCategoryEnum.OTROS
                        ),
                        original_category=tx_data.get("original_category"),
                        categorization_confidence=tx_data.get("confidence"),
                    )
                    db_statement.transactions.append(transaction)

        # Add processing log
        log = ProcessingLog(
            level=LogLevelEnum.INFO
            if extraction_result["success"]
            else LogLevelEnum.ERROR,
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

        # Convert statements to dictionaries
        statements_list = []
        for stmt in statements:
            # Calculate total amount and count from transactions
            stmt_total_transactions = (
                len(stmt.transactions) if stmt.transactions else 0
            )
            # Calculate total amount considering transaction types (credits - debits)
            stmt_total_amount = 0.0
            stmt_total_credits = 0.0
            stmt_total_debits = 0.0
            
            if stmt.transactions:
                for tx in stmt.transactions:
                    if tx.amount is not None:
                        amount = float(tx.amount)
                        if tx.transaction_type == TransactionTypeEnum.CARGO:
                            stmt_total_debits += amount  # Sum debits
                            stmt_total_amount -= amount  # Subtract debits from total
                        else:
                            stmt_total_credits += amount  # Sum credits
                            stmt_total_amount += amount  # Add credits to total

            # Format statement period if available
            stmt_period = None
            if stmt.statement_period_start and stmt.statement_period_end:
                start = stmt.statement_period_start.strftime("%Y-%m-%d")
                end = stmt.statement_period_end.strftime("%Y-%m-%d")
                stmt_period = f"{start} to {end}"

            # Map transactions to dictionaries
            transactions_list = []
            for tx in stmt.transactions or []:
                tx_dict = {
                    "operation_date": tx.operation_date,
                    "charge_date": tx.charge_date,
                    "description": tx.description or "",
                    "amount": (
                        float(tx.amount) if tx.amount is not None else 0.0
                    ),
                    "transaction_type": (
                        TransactionType.DEBIT
                        if tx.transaction_type == TransactionTypeEnum.CARGO
                        else TransactionType.CREDIT
                    ),
                    "category": tx.category or TransactionCategoryEnum.OTROS,
                    "original_category": tx.original_category,
                    "categorization_confidence": tx.categorization_confidence,
                }
                transactions_list.append(tx_dict)

            stmt_dict = {
                "id": stmt.id,  # For frontend compatibility
                "statement_id": stmt.id,  # For API clarity
                "filename": stmt.filename,
                "upload_date": stmt.upload_date,
                "bank_name": stmt.bank_name,
                "customer_name": stmt.customer_name or "",
                "statement_period": stmt_period,
                "total_transactions": stmt_total_transactions,
                "total_amount": stmt_total_amount,
                "total_credits": stmt_total_credits,
                "total_debits": stmt_total_debits,
                "extraction_method": (
                    stmt.extraction_method or "MEXICAN_TEMPLATE"
                ),
                "confidence": float(stmt.overall_confidence or 0.0),
                "transactions": transactions_list,
            }
            statements_list.append(stmt_dict)

        # Create and return the response
        return StatementListResponse(
            statements=statements_list,
            total_count=total,
            page=page,
            per_page=per_page,
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
        # Query the database for the statement
        statement = (
            db.query(BankStatement)
            .filter(BankStatement.id == statement_id)
            .first()
        )
        
        if not statement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Statement with ID {statement_id} not found",
            )

        # Calculate totals from transactions if available
        total_amount = None
        total_debits = None
        total_credits = None
        total_transactions = 0
        
        if hasattr(statement, "transactions") and statement.transactions:
            total_transactions = len(statement.transactions)
            
            # Calculate separate totals for credits and debits
            credits_total = sum(
                float(tx.amount)
                for tx in statement.transactions
                if tx.amount is not None and tx.transaction_type == TransactionTypeEnum.ABONO
            )
            debits_total = sum(
                abs(float(tx.amount))  # Make debits positive for display
                for tx in statement.transactions
                if tx.amount is not None and tx.transaction_type == TransactionTypeEnum.CARGO
            )
            
            total_credits = credits_total
            total_debits = debits_total
            total_amount = credits_total - debits_total  # Net amount (credits - debits)

        # Format statement period if available
        statement_period = None
        if (
            statement.statement_period_start
            and statement.statement_period_end
        ):
            start = statement.statement_period_start.strftime("%Y-%m-%d")
            end = statement.statement_period_end.strftime("%Y-%m-%d")
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
                "transaction_type": TransactionType.DEBIT
                if tx.transaction_type == TransactionTypeEnum.CARGO
                else TransactionType.CREDIT,
            }
            mapped_transactions.append(tx_dict)

        # Create and return the response
        return StatementDetailResponse(
            id=statement.id,  # For frontend compatibility
            statement_id=statement.id,
            filename=statement.filename,
            upload_date=statement.upload_date,
            bank_name=statement.bank_name,
            customer_name=statement.customer_name,
            statement_period=statement_period,
            statement_period_start=statement.statement_period_start,
            statement_period_end=statement.statement_period_end,
            total_transactions=total_transactions,
            total_amount=(
                Decimal(str(total_amount))
                if total_amount is not None
                else None
            ),
            total_debits=(
                Decimal(str(total_debits))
                if total_debits is not None
                else None
            ),
            total_credits=(
                Decimal(str(total_credits))
                if total_credits is not None
                else None
            ),
            extraction_method=(
                statement.extraction_method
                or ExtractionMethod.MEXICAN_TEMPLATE
            ),
            confidence=statement.overall_confidence or 0.0,
            transactions=mapped_transactions,
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
        # Query the database for the statement
        statement = (
            db.query(BankStatement)
            .filter(BankStatement.id == statement_id)
            .first()
        )
        
        if not statement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Statement with ID {statement_id} not found",
            )

        # Delete the statement (cascading deletes will handle related records)
        db.delete(statement)
        db.commit()
        
        logger.info(
            f"Successfully deleted statement {statement_id}: "
            f"{statement.filename}"
        )
        
        # Return 204 No Content (successful deletion)
        return

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
    description=(
        "Test the Mexican template parser with a PDF file "
        "(development endpoint)"
    ),
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
        result = pdf_processor.process_statement(file_content, file.filename)

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


@router.post(
    "/bulk-delete",
    response_model=BulkOperationResponse,
    summary="Bulk delete statements",
    description="Delete multiple statements at once",
)
async def bulk_delete_statements(
    request: BulkDeleteRequest, db: Session = Depends(get_db)
) -> BulkOperationResponse:
    """
    Delete multiple statements at once.

    - **statement_ids**: List of statement IDs to delete (max 100)
    """

    try:
        processed_count = 0
        failed_count = 0
        failed_ids = []

        # Validate input
        if not request.statement_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No statement IDs provided",
            )

        logger.info(
            f"Starting bulk delete for {len(request.statement_ids)} statements"
        )

        # Process each statement ID
        for statement_id in request.statement_ids:
            try:
                # Query the database for the statement
                statement = (
                    db.query(BankStatement)
                    .filter(BankStatement.id == statement_id)
                    .first()
                )

                if not statement:
                    logger.warning(f"Statement {statement_id} not found")
                    failed_count += 1
                    failed_ids.append(statement_id)
                    continue

                # Delete the statement
                filename = statement.filename  # Store for logging
                db.delete(statement)
                processed_count += 1

                logger.debug(f"Deleted statement {statement_id}: {filename}")

            except Exception as e:
                logger.error(f"Error deleting statement {statement_id}: {e}")
                failed_count += 1
                failed_ids.append(statement_id)
                # Continue with other statements rather than failing completely

        # Commit all deletions at once
        if processed_count > 0:
            db.commit()
            logger.info(f"Successfully deleted {processed_count} statements")
        else:
            logger.warning("No statements were deleted")

        # Prepare response
        success = processed_count > 0
        if failed_count == 0:
            message = f"Successfully deleted {processed_count} statements"
        elif processed_count == 0:
            message = f"Failed to delete all {failed_count} statements"
        else:
            message = (
                f"Deleted {processed_count} statements, "
                f"failed to delete {failed_count}"
            )

        return BulkOperationResponse(
            success=success,
            message=message,
            processed_count=processed_count,
            failed_count=failed_count,
            failed_ids=failed_ids,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk delete operation: {e}")
        db.rollback()  # Rollback in case of error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during bulk delete operation",
        )


@router.get(
    "/{statement_id}/transactions",
    response_model=list,
    summary="Get statement transactions",
    description="Retrieve all transactions for a specific statement",
)
async def get_statement_transactions(
    statement_id: int, db: Session = Depends(get_db)
):
    """
    Get all transactions for a specific statement.

    - **statement_id**: ID of the statement to retrieve transactions for
    """
    try:
        # Query the database for the statement
        statement = (
            db.query(BankStatement)
            .filter(BankStatement.id == statement_id)
            .first()
        )
        
        if not statement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Statement with ID {statement_id} not found",
            )

        # Map transactions to API format
        transactions = []
        for tx in statement.transactions or []:
            tx_dict = {
                "id": tx.id,
                "operation_date": tx.operation_date,
                "charge_date": tx.charge_date,
                "transaction_date": tx.operation_date,  # For frontend compatibility
                "description": tx.description,
                "amount": float(tx.amount) if tx.amount else 0.0,
                "transaction_type": (
                    "debit" if tx.transaction_type == TransactionTypeEnum.CARGO
                    else "credit"
                ),
                "category": tx.category,
                "original_category": tx.original_category,
                "categorization_confidence": tx.categorization_confidence,
                "categorization_method": "auto"  # Default value
            }
            transactions.append(tx_dict)

        return transactions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transactions for statement {statement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error retrieving transactions",
        )


@router.get(
    "/{statement_id}/analysis",
    response_model=dict,
    summary="Get statement analysis",
    description="Retrieve analysis data for a specific statement",
)
async def get_statement_analysis(
    statement_id: int, db: Session = Depends(get_db)
):
    """
    Get analysis data for a specific statement.

    - **statement_id**: ID of the statement to retrieve analysis for
    """
    try:
        # Query the database for the statement
        statement = (
            db.query(BankStatement)
            .filter(BankStatement.id == statement_id)
            .first()
        )
        
        if not statement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Statement with ID {statement_id} not found",
            )

        # Calculate analysis data
        transactions = statement.transactions or []
        
        # Basic totals
        total_transactions = len(transactions)
        total_debits = sum(
            float(tx.amount) for tx in transactions
            if tx.transaction_type == TransactionTypeEnum.CARGO and tx.amount
        )
        total_credits = sum(
            float(tx.amount) for tx in transactions
            if tx.transaction_type == TransactionTypeEnum.ABONO and tx.amount
        )
        net_amount = total_credits - total_debits
        
        # Category analysis
        categories = {}
        for tx in transactions:
            category = tx.category or TransactionCategoryEnum.OTROS
            if category not in categories:
                categories[category] = {
                    "category": category,
                    "transaction_count": 0,
                    "total_amount": 0.0,
                    "transactions": []
                }
            
            categories[category]["transaction_count"] += 1
            categories[category]["total_amount"] += float(tx.amount) if tx.amount else 0.0
            categories[category]["transactions"].append(tx)

        # Calculate averages and percentages
        category_list = []
        for category, data in categories.items():
            category_data = {
                "category": category,
                "transaction_count": data["transaction_count"],
                "total_amount": data["total_amount"],
                "average_amount": (
                    data["total_amount"] / data["transaction_count"]
                    if data["transaction_count"] > 0 else 0.0
                ),
                "percentage_of_total": (
                    (data["total_amount"] / abs(total_debits)) * 100
                    if total_debits != 0 else 0.0
                )
            }
            category_list.append(category_data)

        # Sort categories by total amount (descending)
        category_list.sort(key=lambda x: x["total_amount"], reverse=True)

        analysis = {
            "total_transactions": total_transactions,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "net_amount": net_amount,
            "categories": category_list,
            "statement_id": statement_id
        }

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis for statement {statement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error retrieving analysis",
        )


@router.post(
    "/bulk-download",
    summary="Bulk download statements",
    description="Download multiple statements data as CSV",
)
async def bulk_download_statements(
    request: BulkDownloadRequest, db: Session = Depends(get_db)
):
    """
    Download multiple statements data as CSV.

    - **statement_ids**: List of statement IDs to download (max 50)
    """

    try:
        # Validate input
        if not request.statement_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No statement IDs provided",
            )

        logger.info(
            f"Starting bulk download for {len(request.statement_ids)} "
            f"statements"
        )

        # Query statements
        statements = (
            db.query(BankStatement)
            .filter(BankStatement.id.in_(request.statement_ids))
            .all()
        )

        if not statements:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No statements found with the provided IDs",
            )

        # Create CSV content
        csv_content = (
            "ID,Filename,Bank Name,Customer Name,Upload Date,"
            "Period Start,Period End,Total Transactions,Total Amount,Status\n"
        )
        
        for stmt in statements:
            # Format data for CSV
            upload_date = (
                stmt.upload_date.strftime("%Y-%m-%d %H:%M:%S")
                if stmt.upload_date else ""
            )
            period_start = (
                stmt.statement_period_start.strftime("%Y-%m-%d")
                if stmt.statement_period_start else ""
            )
            period_end = (
                stmt.statement_period_end.strftime("%Y-%m-%d")
                if stmt.statement_period_end else ""
            )
            
            # Calculate total transactions and amount
            total_transactions = (
                len(stmt.transactions) if stmt.transactions else 0
            )
            total_amount = sum(
                float(tx.amount) for tx in (stmt.transactions or []) 
                if tx.amount is not None
            )
            
            # Escape commas in text fields
            bank_name = (stmt.bank_name or "").replace(",", ";")
            customer_name = (stmt.customer_name or "").replace(",", ";")
            filename = (stmt.filename or "").replace(",", ";")
            
            csv_content += (
                f"{stmt.id},{filename},{bank_name},{customer_name},"
                f"{upload_date},{period_start},{period_end},"
                f"{total_transactions},{total_amount:.2f},"
                f"{stmt.processing_status or 'unknown'}\n"
            )

        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"statements_export_{timestamp}.csv"

        logger.info(f"Generated CSV for {len(statements)} statements")

        # Return CSV file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk download operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during bulk download operation",
        )
