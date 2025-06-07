#!/usr/bin/env python
"""
Test script for the universal Mexican credit card statement parser
"""
import os
import logging
from pprint import pprint
from app.services.pdf_parser import PDFStatementParser

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_parser(pdf_path):
    """Test the universal parser with a sample statement"""
    print(f"\n=== Testing universal parser with: {os.path.basename(pdf_path)} ===\n")
    
    # Initialize parser
    parser = PDFStatementParser()
    
    # Parse the statement
    try:
        result = parser.parse_pdf(pdf_path)
        
        # Print the parsed data
        print("\n=== Parsing Results ===\n")
        print(f"Bank: {result.get('bank_name', 'Unknown')}")
        print(f"Account Holder: {result.get('account_holder', 'Unknown')}")
        print(f"Account Number: {result.get('account_number', 'Unknown')}")
        print(f"Statement Period: {result.get('statement_period_start', 'Unknown')} to {result.get('statement_period_end', 'Unknown')}")
        print(f"Parsing Confidence: {result.get('parsing_confidence', 0)}")
        print(f"Parsing Method: {result.get('parsing_method', 'Unknown')}")
        
        # Print transaction summary
        transactions = result.get('transactions', [])
        print(f"\nTransactions: {len(transactions)}")
        
        if transactions:
            print("\nSample Transactions:")
            for i, tx in enumerate(transactions[:5], 1):
                print(f"{i}. Date: {tx.get('transaction_date')} | "
                      f"Description: {tx.get('description', '')[:30]}... | "
                      f"Amount: {tx.get('amount')} | "
                      f"Type: {tx.get('transaction_type')}")
            
            if len(transactions) > 5:
                print(f"... and {len(transactions) - 5} more transactions")
        
        # Print summary info
        summary = result.get('summary', {})
        if summary:
            print("\nStatement Summary:")
            for key, value in summary.items():
                print(f"{key}: {value}")
        
        return True
    
    except Exception as e:
        print(f"Error testing parser: {e}")
        return False

if __name__ == "__main__":
    # Test with a sample statement
    sample_pdf = "/Users/ferdinandbracho/code/projects/statement-sense/uploads/file-1.pdf"
    
    if os.path.exists(sample_pdf):
        test_parser(sample_pdf)
    else:
        print(f"Sample PDF not found: {sample_pdf}")
        # Try to find any PDF in the uploads directory
        uploads_dir = "/Users/ferdinandbracho/code/projects/statement-sense/uploads"
        if os.path.exists(uploads_dir):
            pdf_files = [os.path.join(uploads_dir, f) for f in os.listdir(uploads_dir) 
                        if f.lower().endswith('.pdf')]
            
            if pdf_files:
                print(f"Testing with alternative PDF: {pdf_files[0]}")
                test_parser(pdf_files[0])
            else:
                print("No PDF files found in uploads directory")
