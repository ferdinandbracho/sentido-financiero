#!/usr/bin/env python3
"""
Test script to verify PDF parser transaction date extraction
"""
import os
import logging
from app.services.pdf_parser import PDFStatementParser

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pdf_parser():
    """Test the PDF parser to ensure transaction_date is properly extracted"""
    logger.info("Initializing PDF parser...")
    parser = PDFStatementParser()
    
    # Find sample PDFs in the uploads directory
    uploads_dir = os.path.join('uploads')
    if not os.path.exists(uploads_dir):
        logger.error(f"Uploads directory not found: {uploads_dir}")
        return
    
    # List PDF files in uploads directory
    pdf_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logger.warning("No PDF files found in uploads directory")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to test")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(uploads_dir, pdf_file)
        logger.info(f"Testing PDF: {pdf_file}")
        
        try:
            # Parse the PDF
            result = parser.parse_pdf(pdf_path)
            
            # Check if parsing was successful
            if not result:
                logger.error(f"Failed to parse PDF: {pdf_file}")
                continue
            
            # Check if transactions were extracted
            transactions = result.get('transactions', [])
            if not transactions:
                logger.warning(f"No transactions found in PDF: {pdf_file}")
                continue
            
            logger.info(f"Successfully extracted {len(transactions)} transactions")
            
            # Check if transaction_date is present in each transaction
            missing_dates = 0
            for i, transaction in enumerate(transactions[:5]):  # Check first 5 transactions
                if 'transaction_date' not in transaction:
                    missing_dates += 1
                    logger.error(f"Transaction {i} missing transaction_date: {transaction}")
                else:
                    logger.info(f"Transaction {i} has transaction_date: {transaction['transaction_date']}")
            
            if missing_dates:
                logger.error(f"{missing_dates} transactions missing transaction_date field")
            else:
                logger.info("All transactions have transaction_date field - FIX SUCCESSFUL!")
                
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {str(e)}")

if __name__ == "__main__":
    test_pdf_parser()
