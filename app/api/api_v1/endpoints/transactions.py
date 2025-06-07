from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.statement import Transaction
from app.schemas.statement import TransactionResponse, TransactionUpdate
from app.crud import CRUDBase

router = APIRouter()
logger = settings.get_logger(__name__)

# CRUD instance
transaction_crud = CRUDBase[Transaction, None, TransactionUpdate](Transaction)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db)
) -> TransactionResponse:
    """
    Get a specific transaction by ID
    """
    transaction = transaction_crud.get(db, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: UUID,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db)
) -> TransactionResponse:
    """
    Update a transaction (mainly for manual category corrections)
    """
    db_transaction = transaction_crud.get(db, transaction_id)
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # If category is being updated manually, mark it as manual categorization
    if transaction_update.category and transaction_update.category != db_transaction.category:
        transaction_update.categorization_method = "manual"
        transaction_update.confidence_score = 1.0
        logger.info(f"Transaction {transaction_id} category updated manually to: {transaction_update.category}")
    
    updated_transaction = transaction_crud.update(
        db, 
        db_obj=db_transaction, 
        obj_in=transaction_update
    )
    
    return updated_transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a specific transaction
    """
    db_transaction = transaction_crud.get(db, transaction_id)
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    statement_id = db_transaction.statement_id
    transaction_crud.remove(db, id=transaction_id)
    
    logger.info(f"Transaction {transaction_id} deleted from statement {statement_id}")
