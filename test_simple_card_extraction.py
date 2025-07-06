#!/usr/bin/env python3
"""
Simple test for card extraction from OCR text.
"""

import sys
import os
import io
import re
import pdfplumber
import pytesseract

def test_card_extraction_from_ocr():
    """Test card extraction from direct OCR."""
    pdf_path = "/Users/ferdinandbracho/code/projects/statement-sense/.windsurf/Estado de cuenta mayo 2025.pdf"
    
    print(f"Testing card extraction from OCR text")
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
        
        # Test the updated patterns
        print("\nTesting updated card extraction patterns...")
        
        # Patterns from the updated OCR table parser
        card_patterns = [
            # Mexican format patterns
            r'[Nn][úu]?mero de tarjeta[\s:]*(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})',
            r'(?:[Tt]arjeta|[Cc]uenta)[\s:]*(?:[Nn][úu]?m\.?|[Nn][úu]?mero)?[\s:]*(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})',
            # General patterns
            r'(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})',  # Full card number
            r'(\*{12}\d{4})',  # Masked card number
            r'(XXXX[\s-]*XXXX[\s-]*XXXX[\s-]*\d{4})'  # X-masked card number
        ]
        
        extracted_last_four = None
        
        for pattern_num, pattern in enumerate(card_patterns, 1):
            print(f"\nPattern {pattern_num}: {pattern}")
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                card_number = match.group(1) if match.lastindex else match.group()
                clean_card = card_number.replace(" ", "").replace("-", "")
                
                print(f"  ✓ Found: {card_number} -> Clean: {clean_card}")
                
                # Validate card number format and extract last 4 digits
                if re.match(r'^\d{16}$', clean_card):  # Full 16-digit card
                    extracted_last_four = clean_card[-4:]
                    print(f"  ✓ Valid 16-digit card -> Last 4: {extracted_last_four}")
                    break
                elif re.match(r'^\*{12}\d{4}$', clean_card):  # Masked format
                    extracted_last_four = clean_card[-4:]
                    print(f"  ✓ Valid masked card -> Last 4: {extracted_last_four}")
                    break
                else:
                    # Extract last 4 digits from any pattern that has digits
                    last_four = re.findall(r'\d{4}', card_number)[-1] if re.findall(r'\d{4}', card_number) else None
                    if last_four:
                        extracted_last_four = last_four
                        print(f"  ✓ Extracted last 4 from digits: {extracted_last_four}")
                        break
            else:
                print(f"  ✗ No match")
        
        print(f"\nFINAL RESULT:")
        if extracted_last_four:
            print(f"✓ SUCCESS: Card last 4 digits: {extracted_last_four}")
        else:
            print("✗ FAILED: No card last 4 digits extracted")
            
            # Show context around card-related keywords
            print("\nDEBUG: Context around card keywords:")
            lines = ocr_text.split('\n')
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['tarjeta', 'numero', 'no.', 'núm']):
                    print(f"Line {i}: {line.strip()}")
                    # Show surrounding lines
                    for j in range(max(0, i-1), min(len(lines), i+2)):
                        if j != i:
                            print(f"Line {j}: {lines[j].strip()}")
                    print()

if __name__ == "__main__":
    test_card_extraction_from_ocr()