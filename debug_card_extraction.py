#!/usr/bin/env python3
"""
Debug script to test card number extraction from the problematic PDF.
This script will help identify why card_number_last4 is returning null.
"""

import sys
import os
import re
import pdfplumber
import pytesseract
from PIL import Image
import pdf2image
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import services.mexican_parser as mp

def test_pdf_extraction(pdf_path: str):
    """Test card number extraction from PDF."""
    print(f"Testing PDF: {pdf_path}")
    print("-" * 50)
    
    # Read PDF content
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Extract text using pdfplumber
    print("1. Extracting text with pdfplumber...")
    text_content = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                print(f"Page {page_num + 1} text length: {len(page_text)}")
                if page_num == 0:  # Focus on first page where card info usually is
                    print("First 1000 chars of page 1:")
                    print(repr(page_text[:1000]))
                    print()
                text_content += page_text + "\n"
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")
    
    # If no text found, try OCR
    if not text_content.strip():
        print("\nText extraction failed, trying OCR...")
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(pdf_path, dpi=300, first_page=1, last_page=2)
            
            for i, image in enumerate(images):
                print(f"Processing page {i + 1} with OCR...")
                # Use OCR to extract text
                ocr_text = pytesseract.image_to_string(image, lang='spa')
                print(f"OCR text length: {len(ocr_text)}")
                if i == 0:  # Show first page sample
                    print("First 1000 chars of OCR page 1:")
                    print(repr(ocr_text[:1000]))
                    print()
                text_content += ocr_text + "\n"
        except Exception as e:
            print(f"OCR extraction failed: {e}")
    
    # Test Mexican parser patterns
    print("2. Testing Mexican parser patterns...")
    
    # Test current card number pattern
    current_pattern = r"[Nn]úmero de tarjeta:\s*(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})"
    print(f"Current pattern: {current_pattern}")
    
    card_match = re.search(current_pattern, text_content, re.IGNORECASE)
    if card_match:
        card_number = card_match.group(1).replace(" ", "")
        print(f"Found card number: {card_number}")
        print(f"Last 4 digits: {card_number[-4:] if len(card_number) >= 4 else 'N/A'}")
    else:
        print("No match with current pattern")
    
    # Test alternative patterns
    print("\n3. Testing alternative patterns...")
    
    alternative_patterns = [
        r"(?:tarjeta|cuenta|contrato)[\s:]*(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})",  # More flexible
        r"(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})",  # Any 16-digit sequence
        r"\*{12}(\d{4})",  # Masked format
        r"XXXX[\s-]*XXXX[\s-]*XXXX[\s-]*(\d{4})",  # X-masked format
        r"(?:No\.?|Núm\.?|Número)[\s:]*(?:de[\s:]*)?(?:tarjeta|cuenta|contrato)[\s:]*(\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4})"  # Various prefixes
    ]
    
    for i, pattern in enumerate(alternative_patterns, 1):
        print(f"Pattern {i}: {pattern}")
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    card_num = ''.join(match).replace(" ", "").replace("-", "")
                else:
                    card_num = match.replace(" ", "").replace("-", "")
                print(f"  Found: {card_num} (last 4: {card_num[-4:] if len(card_num) >= 4 else 'N/A'})")
        else:
            print(f"  No matches")
    
    # Search for any sequences that look like card numbers
    print("\n4. Searching for any 16-digit sequences...")
    digit_sequences = re.findall(r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}', text_content)
    if digit_sequences:
        print(f"Found {len(digit_sequences)} 16-digit sequences:")
        for seq in digit_sequences:
            clean_seq = seq.replace(" ", "").replace("-", "")
            print(f"  {seq} -> last 4: {clean_seq[-4:]}")
    else:
        print("No 16-digit sequences found")
    
    # Search for masked card numbers
    print("\n5. Searching for masked card numbers...")
    masked_patterns = [
        r'\*{12}\d{4}',
        r'XXXX[\s-]*XXXX[\s-]*XXXX[\s-]*\d{4}',
        r'\*{4}[\s-]*\*{4}[\s-]*\*{4}[\s-]*\d{4}'
    ]
    
    for pattern in masked_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        if matches:
            print(f"Pattern {pattern}: {matches}")
            for match in matches:
                last_four = re.findall(r'\d{4}', match)[-1] if re.findall(r'\d{4}', match) else None
                if last_four:
                    print(f"  Last 4 digits: {last_four}")
    
    # Look for card-related text
    print("\n6. Looking for card-related keywords...")
    card_keywords = ['tarjeta', 'cuenta', 'contrato', 'número', 'no.', 'núm']
    for keyword in card_keywords:
        if keyword.lower() in text_content.lower():
            print(f"Found keyword: {keyword}")
            # Get context around the keyword
            lines = text_content.split('\n')
            for line_num, line in enumerate(lines):
                if keyword.lower() in line.lower():
                    print(f"  Line {line_num}: {line.strip()}")
                    break
    
    print("\n" + "="*50)

if __name__ == "__main__":
    pdf_path = "/Users/ferdinandbracho/code/projects/statement-sense/.windsurf/Estado de cuenta mayo 2025.pdf"
    
    if os.path.exists(pdf_path):
        test_pdf_extraction(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")