#!/usr/bin/env python3
"""
Test the updated card extraction patterns.
"""

import sys
import os
import re
import io
import pdfplumber
import pytesseract

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.mexican_parser import MexicanStatementParser

def test_updated_patterns(pdf_path: str):
    """Test the updated card extraction patterns."""
    print(f"Testing updated patterns with: {pdf_path}")
    print("-" * 50)
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    pdf_file = io.BytesIO(pdf_content)
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            # Test on page 2 where we found the card number
            page = pdf.pages[1]  # Page 2 (0-indexed)
            
            print("Converting page 2 to image for OCR...")
            pil_image = page.to_image(resolution=300).original
            
            print("Running OCR...")
            ocr_text = pytesseract.image_to_string(
                pil_image,
                lang='spa+eng',
                config='--psm 6'
            )
            
            print(f"OCR extracted {len(ocr_text)} characters")
            
            # Test the updated Mexican parser
            print("\nTesting updated Mexican parser...")
            parser = MexicanStatementParser()
            customer_info = parser.extract_customer_info(ocr_text)
            
            print(f"Extracted info: {customer_info}")
            
            if customer_info.get("card_number"):
                card_number = customer_info["card_number"]
                last_four = card_number[-4:] if len(card_number) >= 4 else None
                print(f"✓ SUCCESS: Found card number: {card_number}")
                print(f"✓ Last 4 digits: {last_four}")
            else:
                print("✗ Failed to extract card number")
                
                # Show what patterns are being tested
                print("\nDebug: Testing individual patterns...")
                
                # Test the main pattern
                main_pattern = r"[Nn][úu]mero de tarjeta:\s*(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})"
                match = re.search(main_pattern, ocr_text, re.IGNORECASE)
                if match:
                    print(f"Main pattern matched: {match.group(1)}")
                else:
                    print("Main pattern did not match")
                    
                # Test fallback patterns
                fallback_patterns = [
                    r"(?:[Tt]arjeta|[Cc]uenta)[\s:]*(?:[Nn][úu]?m\.?|[Nn][úu]?mero)?[\s:]*(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})",
                    r"(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})",
                ]
                
                for i, pattern in enumerate(fallback_patterns, 1):
                    match = re.search(pattern, ocr_text, re.IGNORECASE)
                    if match:
                        card_num = match.group(1).replace(" ", "")
                        print(f"Fallback pattern {i} matched: {card_num}")
                        if re.match(r'^[3-6]\d{15}$', card_num):
                            print(f"  Valid card number format")
                        else:
                            print(f"  Invalid card number format")
                    else:
                        print(f"Fallback pattern {i} did not match")
                
                # Show context around "tarjeta"
                print("\nContext around 'tarjeta':")
                lines = ocr_text.split('\n')
                for i, line in enumerate(lines):
                    if 'tarjeta' in line.lower():
                        print(f"Line {i}: {line.strip()}")
                        if i > 0:
                            print(f"Line {i-1}: {lines[i-1].strip()}")
                        if i < len(lines) - 1:
                            print(f"Line {i+1}: {lines[i+1].strip()}")
                        print()
    
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    pdf_path = "/Users/ferdinandbracho/code/projects/statement-sense/.windsurf/Estado de cuenta mayo 2025.pdf"
    
    if os.path.exists(pdf_path):
        test_updated_patterns(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")