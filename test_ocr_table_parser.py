#!/usr/bin/env python3
"""
Test the OCR table parser with enhanced debugging.
"""

import sys
import os
import io
import pdfplumber

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.ocr_table_parser import OCRTableParser
from models.statement import BankStatement

def test_ocr_table_parser(pdf_path: str):
    """Test the OCR table parser for card extraction."""
    print(f"Testing OCR table parser with: {pdf_path}")
    print("-" * 60)
    
    # Create a mock statement object
    statement = BankStatement()
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Initialize the OCR table parser
    parser = OCRTableParser()
    
    try:
        # Parse header information from the first few pages
        print("Testing header parsing with OCR table parser...")
        
        pdf_file = io.BytesIO(pdf_content)
        with pdfplumber.open(pdf_file) as pdf:
            # Get OCR text from the first few pages
            ocr_text_combined = ""
            
            for page_num in range(min(3, len(pdf.pages))):
                print(f"\nProcessing page {page_num + 1}...")
                page = pdf.pages[page_num]
                
                # Extract raw text using OCR
                try:
                    import pytesseract
                    pil_image = page.to_image(resolution=300).original
                    page_text = pytesseract.image_to_string(
                        pil_image,
                        lang='spa+eng',
                        config='--psm 6'
                    )
                    print(f"Page {page_num + 1} OCR text length: {len(page_text)}")
                    
                    # Look for card patterns in this page
                    import re
                    card_patterns = [
                        r'[Nn][úu]?mero de tarjeta[\s:]*(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})',
                        r'(?:[Tt]arjeta|[Cc]uenta)[\s:]*(?:[Nn][úu]?m\.?|[Nn][úu]?mero)?[\s:]*(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})',
                        r'(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})',
                    ]
                    
                    for pattern_num, pattern in enumerate(card_patterns, 1):
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            card_number = match.group(1) if match.lastindex else match.group()
                            clean_card = card_number.replace(" ", "").replace("-", "")
                            print(f"  Pattern {pattern_num} found card: {clean_card}")
                            if len(clean_card) == 16:
                                print(f"  -> Last 4 digits: {clean_card[-4:]}")
                    
                    ocr_text_combined += page_text + "\n"
                    
                except Exception as e:
                    print(f"OCR failed for page {page_num + 1}: {e}")
        
        # Test the actual _parse_header_info method
        print(f"\nTesting _parse_header_info method...")
        parser._parse_header_info(statement, ocr_text_combined)
        
        print(f"Result: card_last_four = {statement.card_last_four}")
        print(f"Result: customer_name = {statement.customer_name}")
        
        if statement.card_last_four:
            print(f"✓ SUCCESS: Card last 4 extracted: {statement.card_last_four}")
        else:
            print("✗ FAILED: Card last 4 not extracted")
            
            # Debug: show what text is being processed
            print("\nDEBUG: First 2000 chars of combined text:")
            print(repr(ocr_text_combined[:2000]))
    
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    pdf_path = "/Users/ferdinandbracho/code/projects/statement-sense/.windsurf/Estado de cuenta mayo 2025.pdf"
    
    if os.path.exists(pdf_path):
        test_ocr_table_parser(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")