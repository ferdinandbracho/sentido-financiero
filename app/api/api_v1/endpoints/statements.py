import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import CRUDBase
from app.db.session import get_db
from app.models.statement import BankStatement, Transaction
from app.schemas.statement import (
    BankStatementResponse,
    BankStatementSummary,
    FileUploadResponse,
    ProcessingStatusResponse,
    SpendingAnalysis,
    TransactionResponse,
)
from app.services.pdf_parser import PDFStatementParser
from app.services.smart_categorizer import SmartCategorizer

router = APIRouter()
logger = settings.get_logger(__name__)

# CRUD instances
statement_crud = CRUDBase[BankStatement, None, None](BankStatement)
transaction_crud = CRUDBase[Transaction, None, None](Transaction)

# Service instances  
pdf_parser = PDFStatementParser()
categorizer = SmartCategorizer(ollama_url=os.getenv('OLLAMA_URL', 'http://localhost:11434'))

# Ensure upload directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> FileUploadResponse:
    """
    Upload a PDF bank statement for processing
    """
    logger.info(f"Uploading file: {file.filename}")
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PDF"
        )
    
    # Validate file size (50MB limit)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo excede el límite de 50MB"
        )
    
    try:
        # Save file to a temporary location for parsing
        temp_file_path = UPLOAD_DIR / f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(content)
        
        # Parse the PDF to get bank and period info
        pdf_parser = PDFStatementParser()
        parsed_data = pdf_parser.parse_pdf(str(temp_file_path))
        
        # Clean up temp file
        temp_file_path.unlink()
        
        # Check for existing statement with same bank and period
        if parsed_data.get('bank_name') and parsed_data.get('statement_period_start') and parsed_data.get('statement_period_end'):
            existing_statement = db.query(BankStatement).filter(
                BankStatement.bank_name == parsed_data['bank_name'],
                BankStatement.statement_period_start == parsed_data['statement_period_start'],
                BankStatement.statement_period_end == parsed_data['statement_period_end']
            ).first()
            
            if existing_statement:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": f"Ya existe un estado de cuenta para {parsed_data['bank_name']} del período {parsed_data['statement_period_start'].strftime('%B %Y')}",
                        "statement_id": str(existing_statement.id),
                        "is_duplicate": True
                    }
                )
        
        # Save file to uploads directory with a better name if we have the info
        if parsed_data.get('bank_name') and parsed_data.get('statement_period_start'):
            period = parsed_data['statement_period_start'].strftime('%Y%m')
            bank_slug = parsed_data['bank_name'].lower().replace(' ', '_')
            new_filename = f"{bank_slug}_{period}_{file.filename}"
        else:
            new_filename = file.filename
            
        file_path = UPLOAD_DIR / new_filename
        
        # Ensure unique filename
        counter = 1
        while file_path.exists():
            name_parts = new_filename.rsplit('.', 1)
            new_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            file_path = UPLOAD_DIR / new_filename
            counter += 1
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Create database record with extracted metadata
        statement_data = {
            "filename": new_filename,
            "file_path": str(file_path),
            "file_size": file_size,
            "processing_status": "uploaded",
            "bank_name": parsed_data.get('bank_name'),
            "account_holder": parsed_data.get('account_holder'),
            "account_number": parsed_data.get('account_number'),
            "statement_period_start": parsed_data.get('statement_period_start'),
            "statement_period_end": parsed_data.get('statement_period_end')
        }
        
        db_statement = BankStatement(**statement_data)
        db.add(db_statement)
        db.commit()
        db.refresh(db_statement)
        
        logger.info(f"File uploaded successfully: {db_statement.id}")
        
        return FileUploadResponse(
            statement_id=db_statement.id,
            filename=new_filename,
            file_size=file_size,
            status="uploaded",
            message="Archivo subido correctamente. Usa el botón de procesar para analizar el estado de cuenta.",
            metadata={
                "bank_name": parsed_data.get('bank_name'),
                "statement_period": f"{parsed_data.get('statement_period_start')} - {parsed_data.get('statement_period_end')}" if parsed_data.get('statement_period_start') and parsed_data.get('statement_period_end') else None
            }
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        # Clean up file if database operation failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.post("/{statement_id}/process", response_model=ProcessingStatusResponse)
@router.post("/{statement_id}/process/", response_model=ProcessingStatusResponse, include_in_schema=False)
async def process_statement(
    statement_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> ProcessingStatusResponse:
    """
    Process an uploaded bank statement (PDF parsing + transaction categorization)
    """
    logger.info(f"Processing statement: {statement_id}")
    
    # Get statement from database
    db_statement = statement_crud.get(db, statement_id)
    if not db_statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    if db_statement.processing_status in ["processing", "processed"]:
        return ProcessingStatusResponse(
            statement_id=statement_id,
            status=db_statement.processing_status,
            message=f"Statement is already {db_statement.processing_status}"
        )
    
    # Update status to processing
    db_statement.processing_status = "processing"
    db.commit()
    
    # Add background processing task
    background_tasks.add_task(
        process_statement_background,
        statement_id,
        db_statement.file_path
    )
    
    return ProcessingStatusResponse(
        statement_id=statement_id,
        status="processing",
        message="Statement processing started. Check status with GET /statements/{id}"
    )


async def process_statement_background(statement_id: UUID, file_path: str):
    """
    Background task to process statement
    """
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        logger.info(f"Background processing started for statement: {statement_id}")
        
        # Get statement
        db_statement = statement_crud.get(db, statement_id)
        if not db_statement:
            logger.error(f"Statement not found: {statement_id}")
            return
        
        # Parse PDF
        logger.info("Parsing PDF...")
        extracted_data = pdf_parser.parse_pdf(file_path)
        
        # Update statement with extracted info
        db_statement.bank_name = extracted_data.get('bank_name')
        db_statement.account_holder = extracted_data.get('account_holder')
        db_statement.account_number = extracted_data.get('account_number')
        
        period = extracted_data.get('statement_period', (None, None))
        if period[0]:
            db_statement.statement_period_start = period[0]
        if period[1]:
            db_statement.statement_period_end = period[1]
        
        db_statement.raw_extracted_data = str(extracted_data)
        
        # Process transactions
        transactions = extracted_data.get('transactions', [])
        logger.info(f"Found {len(transactions)} transactions")
        
        if transactions:
            # Categorize transactions
            logger.info("Categorizing transactions...")
            categorized_transactions, stats = await categorizer.categorize_transactions(transactions)
            
            # Save transactions to database
            total_credits = 0.0
            total_debits = 0.0
            
            for trans_data in categorized_transactions:
                # Get transaction date or use fallback to statement period start date or current date
                transaction_date = trans_data.get('transaction_date')
                if not transaction_date:
                    # Try to use date field from PDFStatementParser
                    transaction_date = trans_data.get('date')
                
                # If still no date, use statement period start or current date as fallback
                if not transaction_date:
                    if db_statement.statement_period_start:
                        transaction_date = db_statement.statement_period_start
                        logger.warning(f"Missing transaction date, using statement period start: {transaction_date}")
                    else:
                        transaction_date = datetime.now()
                        logger.warning(f"Missing transaction date, using current date: {transaction_date}")
                
                transaction = Transaction(
                    statement_id=statement_id,
                    transaction_date=transaction_date,  # Use the validated date
                    processing_date=trans_data.get('processing_date'),
                    description=trans_data.get('description', ''),
                    amount=trans_data.get('amount', 0.0),
                    transaction_type=trans_data.get('transaction_type', 'debit'),
                    category=trans_data.get('category'),
                    confidence_score=trans_data.get('confidence'),
                    categorization_method=trans_data.get('categorization_method'),
                    is_recurring=trans_data.get('is_recurring', False),
                    is_transfer=trans_data.get('is_credit', False),
                    merchant_name=trans_data.get('merchant_name'),
                    raw_description=trans_data.get('description')
                )
                
                if transaction.transaction_type == 'credit':
                    total_credits += abs(transaction.amount)
                else:
                    total_debits += abs(transaction.amount)
                
                db.add(transaction)
            
            # Update statement totals
            db_statement.total_transactions = len(transactions)
            db_statement.total_credits = total_credits
            db_statement.total_debits = total_debits
            
            logger.info(f"Categorization stats: {stats}")
        
        # Mark as completed
        db_statement.processing_status = "processed"
        db_statement.processing_notes = f"Successfully processed {len(transactions)} transactions"
        
        db.commit()
        logger.info(f"Statement processing completed: {statement_id}")
        
    except Exception as e:
        logger.error(f"Error processing statement {statement_id}: {str(e)}")
        if db_statement:
            db_statement.processing_status = "failed"
            db_statement.processing_notes = f"Processing failed: {str(e)}"
            db.commit()
    finally:
        db.close()


@router.get("", response_model=List[BankStatementSummary])
@router.get("/", response_model=List[BankStatementSummary], include_in_schema=False)
def list_statements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[BankStatementSummary]:
    """
    Get list of all uploaded statements
    """
    statements = statement_crud.get_multi(db, skip=skip, limit=limit)
    return statements


@router.get("/{statement_id}", response_model=BankStatementResponse)
def get_statement(
    statement_id: UUID,
    db: Session = Depends(get_db)
) -> BankStatementResponse:
    """
    Get detailed information about a specific statement
    """
    from sqlalchemy.orm import joinedload
    from sqlalchemy import text
    
    # Convert UUID to string for direct comparison
    statement_id_str = str(statement_id)
    
    # Use direct string comparison for UUID
    db_statement = db.query(BankStatement).options(
        joinedload(BankStatement.transactions)
    ).filter(text(f"bank_statements.id::text = '{statement_id_str}'")).first()
    
    if not db_statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    return db_statement


@router.get("/{statement_id}/transactions", response_model=List[TransactionResponse])
def get_statement_transactions(
    statement_id: UUID,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
) -> List[TransactionResponse]:
    """
    Get transactions for a specific statement
    """
    from sqlalchemy import text
    
    # Convert UUID to string for direct comparison
    statement_id_str = str(statement_id)
    
    # Verify statement exists
    db_statement = db.query(BankStatement).filter(
        text(f"bank_statements.id::text = '{statement_id_str}'")
    ).first()
    
    if not db_statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    # Build query
    query = db.query(Transaction).filter(
        text(f"transactions.statement_id::text = '{statement_id_str}'")
    )
    
    if category:
        query = query.filter(Transaction.category == category)
    
    transactions = query.offset(skip).limit(limit).all()
    return transactions


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_statement(
    statement_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a statement and all its transactions
    """
    db_statement = statement_crud.get(db, statement_id)
    if not db_statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    # Delete file if it exists
    if db_statement.file_path and Path(db_statement.file_path).exists():
        try:
            Path(db_statement.file_path).unlink()
        except Exception as e:
            logger.warning(f"Could not delete file {db_statement.file_path}: {e}")
    
    # Delete from database (cascade will handle transactions)
    db.delete(db_statement)
    db.commit()
    
    logger.info(f"Statement deleted: {statement_id}")


@router.get("/{statement_id}/analysis", response_model=SpendingAnalysis)
def get_spending_analysis(
    statement_id: UUID,
    db: Session = Depends(get_db)
) -> SpendingAnalysis:
    """
    Get spending analysis for a statement
    """
    from sqlalchemy import text
    
    # Convert UUID to string for direct comparison
    statement_id_str = str(statement_id)
    
    # Verify statement exists
    db_statement = db.query(BankStatement).filter(
        text(f"bank_statements.id::text = '{statement_id_str}'")
    ).first()
    
    if not db_statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    # Get all transactions
    transactions = db.query(Transaction).filter(
        text(f"transactions.statement_id::text = '{statement_id_str}'")
    ).all()
    
    # Generate analysis (this would be implemented in a separate service)
    analysis = generate_spending_analysis(db_statement, transactions)
    return analysis


@router.get("/{statement_id}/download")
async def download_statement(
    statement_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Download the original uploaded PDF statement
    """
    from sqlalchemy import text
    
    # Convert UUID to string for direct comparison
    statement_id_str = str(statement_id)
    
    # Verify statement exists
    db_statement = db.query(BankStatement).filter(
        text(f"bank_statements.id::text = '{statement_id_str}'")
    ).first()
    
    if not db_statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    # Resolve path relative to project root
    from app.config import PROJECT_ROOT
    file_path = PROJECT_ROOT / db_statement.file_path
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=file_path,
        filename=db_statement.filename,
        media_type="application/pdf"
    )

def generate_spending_analysis(statement: BankStatement, transactions: List[Transaction]) -> SpendingAnalysis:
    """
    Generate spending analysis from transactions
    """
    # This is a simplified implementation
    # In practice, this would be a more sophisticated analysis service
    
    from collections import defaultdict
    
    categories = defaultdict(lambda: {'count': 0, 'total': 0.0})
    total_debits = 0.0
    total_credits = 0.0
    
    for trans in transactions:
        if trans.transaction_type == 'debit':
            total_debits += abs(trans.amount)
            categories[trans.category or 'uncategorized']['count'] += 1
            categories[trans.category or 'uncategorized']['total'] += abs(trans.amount)
        else:
            total_credits += abs(trans.amount)
    
    # Convert to schema format
    category_summaries = []
    for cat, data in categories.items():
        category_summaries.append({
            'category': cat,
            'subcategory': None,
            'transaction_count': data['count'],
            'total_amount': data['total'],
            'average_amount': data['total'] / data['count'] if data['count'] > 0 else 0,
            'percentage_of_total': (data['total'] / total_debits * 100) if total_debits > 0 else 0
        })
    
    return SpendingAnalysis(
        statement_id=statement.id,
        analysis_period=f"{statement.statement_period_start} to {statement.statement_period_end}",
        total_transactions=len(transactions),
        total_credits=total_credits,
        total_debits=total_debits,
        net_amount=total_credits - total_debits,
        categories=category_summaries,
        monthly_breakdown=[],  # Would implement proper monthly analysis
        recurring_transactions=[t for t in transactions if t.is_recurring],
        largest_expenses=sorted([t for t in transactions if t.transaction_type == 'debit'], 
                               key=lambda x: abs(x.amount), reverse=True)[:10],
        categorization_stats={}  # Would get from categorizer
    )
