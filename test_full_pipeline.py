#!/usr/bin/env python3
"""
Test the full processing pipeline with the updated card extraction patterns.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.pdf_parser import PDFProcessor

def test_full_pipeline(pdf_path: str):
    """Test the full PDF processing pipeline."""
    print(f"Testing full pipeline with: {pdf_path}")
    print("-" * 60)
    
    # Read the PDF file
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    print(f"PDF file size: {len(pdf_content)} bytes")
    
    # Initialize the PDF processor
    processor = PDFProcessor()
    
    # Process the statement
    print("\nProcessing statement...")
    try:
        result = processor.process_statement(pdf_content)
        
        print(f"Processing result: {result}")
        
        # Check if card_last_four was extracted
        if hasattr(result, 'card_last_four') and result.card_last_four:
            print(f"✓ SUCCESS: Card last 4 digits extracted: {result.card_last_four}")
        else:
            print("✗ FAILED: Card last 4 digits not extracted")
            
        # Print other relevant extracted information
        if hasattr(result, 'customer_name') and result.customer_name:
            print(f"Customer name: {result.customer_name}")
        if hasattr(result, 'bank_name') and result.bank_name:
            print(f"Bank name: {result.bank_name}")
        if hasattr(result, 'statement_date') and result.statement_date:
            print(f"Statement date: {result.statement_date}")
        if hasattr(result, 'due_date') and result.due_date:
            print(f"Due date: {result.due_date}")
            
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    pdf_path = "/Users/ferdinandbracho/code/projects/statement-sense/.windsurf/Estado de cuenta mayo 2025.pdf"
    
    if os.path.exists(pdf_path):
        test_full_pipeline(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")