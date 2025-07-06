#!/usr/bin/env python3
"""
Test OCR extraction using the existing codebase infrastructure.
"""

import sys
import os
import re
import io
import pdfplumber
import pytesseract

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_ocr_extraction(pdf_path: str):
    """Test OCR extraction from PDF using pdfplumber."""
    print(f"Testing OCR extraction from: {pdf_path}")
    print("-" * 50)
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    pdf_file = io.BytesIO(pdf_content)
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            print(f"PDF has {len(pdf.pages)} pages")
            
            # Check first few pages for card info
            for page_num in range(min(3, len(pdf.pages))):
                print(f"\n{'='*60}")
                print(f"PROCESSING PAGE {page_num + 1}")
                print('='*60)
                
                page = pdf.pages[page_num]
                
                # Convert page to image
                print("Converting page to image for OCR...")
                pil_image = page.to_image(resolution=300).original
                
                # Extract text using OCR
                print("Running OCR...")
                ocr_text = pytesseract.image_to_string(
                    pil_image,
                    lang='spa+eng',
                    config='--psm 6'
                )
                
                print(f"OCR extracted {len(ocr_text)} characters")
                print("\nFirst 1000 characters of OCR text:")
                print("=" * 50)
                print(ocr_text[:1000])
                print("=" * 50)
                
                # Test card number patterns
                print("\nTesting card number patterns...")
                
                # Current pattern from mexican_parser.py
                current_pattern = r"[Nn]úmero de tarjeta:\s*(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})"
                print(f"Current pattern: {current_pattern}")
                
                card_match = re.search(current_pattern, ocr_text, re.IGNORECASE)
                if card_match:
                    card_number = card_match.group(1).replace(" ", "")
                    print(f"✓ Found card number: {card_number}")
                    print(f"✓ Last 4 digits: {card_number[-4:]}")
                    return  # Found card number, exit
                else:
                    print("✗ No match with current pattern")
                
                # Test alternative patterns
                print("\nTesting alternative patterns...")
                
                alternative_patterns = [
                    (r"(?:tarjeta|cuenta)[\s:]*(?:No\.?|Núm\.?|Número)?[\s:]*(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})", "Flexible tarjeta/cuenta pattern"),
                    (r"(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})", "Any 16-digit sequence"),
                    (r"\*{12}(\d{4})", "Masked format (*12digits)"),
                    (r"XXXX[\s-]*XXXX[\s-]*XXXX[\s-]*(\d{4})", "X-masked format"),
                    (r"(?:No\.?|Núm\.?|Número)[\s:]*(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})", "Number prefix pattern"),
                    (r"(\*{4}[\s-]*\*{4}[\s-]*\*{4}[\s-]*\d{4})", "Asterisk masked format"),
                    (r"[Tt]arjeta.*?(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})", "Tarjeta followed by digits"),
                ]
                
                found_card = False
                for pattern, description in alternative_patterns:
                    print(f"\nPattern: {description}")
                    print(f"Regex: {pattern}")
                    matches = re.findall(pattern, ocr_text, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            if isinstance(match, tuple):
                                card_num = ''.join(match).replace(" ", "").replace("-", "")
                            else:
                                card_num = match.replace(" ", "").replace("-", "")
                            
                            # Extract last 4 digits
                            if len(card_num) >= 4:
                                last_four = re.findall(r'\d{4}', card_num)[-1] if re.findall(r'\d{4}', card_num) else None
                                print(f"  ✓ Found: {card_num} -> Last 4: {last_four}")
                                found_card = True
                            else:
                                print(f"  ? Found short match: {card_num}")
                    else:
                        print(f"  ✗ No matches")
                
                if found_card:
                    return  # Found card number, exit
                
                # Look for context around potential card numbers
                print("\nLooking for card-related context...")
                lines = ocr_text.split('\n')
                for i, line in enumerate(lines):
                    line_clean = line.strip()
                    if any(keyword in line_clean.lower() for keyword in ['tarjeta', 'cuenta', 'número', 'no.', 'núm']):
                        print(f"Line {i}: {line_clean}")
                        # Check surrounding lines for numbers
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            if j != i and re.search(r'\d{4}', lines[j]):
                                print(f"  Adjacent line {j}: {lines[j].strip()}")
    
    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    pdf_path = "/Users/ferdinandbracho/code/projects/statement-sense/.windsurf/Estado de cuenta mayo 2025.pdf"
    
    if os.path.exists(pdf_path):
        test_ocr_extraction(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")