#!/usr/bin/env python3
"""
Direct card extraction test to verify the issue.
"""

import sys
import os
import io
import re
import pdfplumber
import pytesseract

def test_direct_card_extraction():
    """Test direct card extraction from page 2."""
    pdf_path = "/Users/ferdinandbracho/code/projects/statement-sense/.windsurf/Estado de cuenta mayo 2025.pdf"
    
    print(f"Testing direct card extraction from page 2")
    print("-" * 60)
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    pdf_file = io.BytesIO(pdf_content)
    
    with pdfplumber.open(pdf_file) as pdf:
        # Extract OCR text from page 2 (where we know the card info is)
        page = pdf.pages[1]  # Page 2 (0-indexed)
        
        print("Extracting OCR text from page 2...")
        pil_image = page.to_image(resolution=300).original
        ocr_text = pytesseract.image_to_string(
            pil_image,
            lang='spa+eng',
            config='--psm 6'
        )
        
        print(f"OCR text length: {len(ocr_text)}")
        
        # Look for the exact card pattern we know exists
        print("\nSearching for card number pattern...")
        
        # Test the exact pattern we found working before
        pattern = r'[Nn][úu]?mero de tarjeta[\s:]*(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})'
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        
        if match:
            card_number = match.group(1).replace(" ", "").replace("-", "")
            print(f"✓ Found card number: {card_number}")
            print(f"✓ Last 4 digits: {card_number[-4:]}")
            
            # This should be 5262
            if card_number[-4:] == "5262":
                print("✓ SUCCESS: Card extraction is working correctly")
                return True
            else:
                print(f"✗ ERROR: Expected last 4 digits to be 5262, got {card_number[-4:]}")
                return False
        else:
            print("✗ FAILED: Card number not found with updated pattern")
            
            # Debug: show context around 'numero' or 'tarjeta'
            print("\nDEBUG: Context around card keywords:")
            lines = ocr_text.split('\n')
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['numero', 'tarjeta']):
                    print(f"Line {i}: {line.strip()}")
                    # Show surrounding lines
                    for j in range(max(0, i-1), min(len(lines), i+2)):
                        if j != i:
                            print(f"Line {j}: {lines[j].strip()}")
                    print()
            return False

if __name__ == "__main__":
    success = test_direct_card_extraction()
    exit(0 if success else 1)