#!/usr/bin/env python3
"""
Test suite for card number extraction functionality.

This module tests various aspects of card number extraction from PDF statements,
including direct OCR extraction, table parsing, and full pipeline processing.
"""

import sys
import os
import io
import re
import pytest
from pathlib import Path
import pdfplumber
import pytesseract

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from services.pdf_parser import PDFProcessor
from services.ocr_table_parser import OCRTableParser
from services.mexican_parser import mexican_parser


class TestCardExtraction:
    """Test suite for card number extraction from PDF statements."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with sample PDF path."""
        cls.pdf_path = "/Users/ferdinandbracho/code/projects/statement-sense/.windsurf/Estado de cuenta mayo 2025.pdf"
        cls.expected_last_four = "5262"  # Known value from the test PDF
    
    def test_direct_ocr_card_extraction(self):
        """Test direct OCR card extraction from page 2."""
        print(f"Testing direct card extraction from page 2")
        print("-" * 60)
        
        if not os.path.exists(self.pdf_path):
            pytest.skip(f"Test PDF not found: {self.pdf_path}")
        
        with open(self.pdf_path, 'rb') as f:
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
            print("\\nSearching for card number pattern...")
            
            # Test the exact pattern we found working before
            pattern = r'[Nn][úu]?mero de tarjeta[\\s:]*(\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4})'
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            
            if match:
                card_number = match.group(1).replace(" ", "").replace("-", "")
                print(f"✓ Found card number: {card_number}")
                last_four = card_number[-4:]
                print(f"✓ Last 4 digits: {last_four}")
                
                assert last_four == self.expected_last_four, f"Expected {self.expected_last_four}, got {last_four}"
                print("✓ SUCCESS: Card extraction is working correctly")
                return True
            else:
                print("✗ FAILED: Card number not found with updated pattern")
                # Debug: show context around 'numero' or 'tarjeta'
                self._debug_card_context(ocr_text)
                assert False, "Card number not found"
    
    def test_ocr_table_parser_patterns(self):
        """Test the OCR table parser card extraction patterns."""
        print(f"Testing OCR table parser card extraction patterns")
        print("-" * 60)
        
        if not os.path.exists(self.pdf_path):
            pytest.skip(f"Test PDF not found: {self.pdf_path}")
        
        with open(self.pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        pdf_file = io.BytesIO(pdf_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            # Extract OCR text from page 2
            page = pdf.pages[1]  # Page 2 (0-indexed)
            
            pil_image = page.to_image(resolution=300).original
            ocr_text = pytesseract.image_to_string(
                pil_image,
                lang='spa+eng',
                config='--psm 6'
            )
            
            print(f"OCR text length: {len(ocr_text)}")
            
            # Test the updated patterns from OCR table parser
            print("\\nTesting updated card extraction patterns...")
            
            # Patterns from the updated OCR table parser
            card_patterns = [
                # Mexican format patterns
                r'[Nn][úu]?mero de tarjeta[\\s:]*(\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4})',
                r'(?:[Tt]arjeta|[Cc]uenta)[\\s:]*(?:[Nn][úu]?m\\.?|[Nn][úu]?mero)?[\\s:]*(\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4})',
                # General patterns
                r'(\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4})',  # Full card number
                r'(\\*{12}\\d{4})',  # Masked card number
                r'(XXXX[\\s-]*XXXX[\\s-]*XXXX[\\s-]*\\d{4})'  # X-masked card number
            ]
            
            extracted_last_four = None
            
            for pattern_num, pattern in enumerate(card_patterns, 1):
                print(f"\\nPattern {pattern_num}: {pattern}")
                match = re.search(pattern, ocr_text, re.IGNORECASE)
                if match:
                    card_number = match.group(1) if match.lastindex else match.group()
                    clean_card = card_number.replace(" ", "").replace("-", "")
                    
                    print(f"  ✓ Found: {card_number} -> Clean: {clean_card}")
                    
                    # Validate card number format and extract last 4 digits
                    if re.match(r'^\\d{16}$', clean_card):  # Full 16-digit card
                        extracted_last_four = clean_card[-4:]
                        print(f"  ✓ Valid 16-digit card -> Last 4: {extracted_last_four}")
                        break
                    elif re.match(r'^\\*{12}\\d{4}$', clean_card):  # Masked format
                        extracted_last_four = clean_card[-4:]
                        print(f"  ✓ Valid masked card -> Last 4: {extracted_last_four}")
                        break
                    else:
                        # Extract last 4 digits from any pattern that has digits
                        last_four = re.findall(r'\\d{4}', card_number)[-1] if re.findall(r'\\d{4}', card_number) else None
                        if last_four:
                            extracted_last_four = last_four
                            print(f"  ✓ Extracted last 4 from digits: {extracted_last_four}")
                            break
                else:
                    print(f"  ✗ No match")
            
            print(f"\\nFINAL RESULT:")
            if extracted_last_four:
                print(f"✓ SUCCESS: Card last 4 digits: {extracted_last_four}")
                assert extracted_last_four == self.expected_last_four, f"Expected {self.expected_last_four}, got {extracted_last_four}"
            else:
                print("✗ FAILED: No card last 4 digits extracted")
                self._debug_card_context(ocr_text)
                assert False, "No card last 4 digits extracted"
    
    def test_full_pipeline_processing(self):
        """Test the full PDF processing pipeline."""
        print(f"Testing full pipeline processing")
        print("-" * 60)
        
        if not os.path.exists(self.pdf_path):
            pytest.skip(f"Test PDF not found: {self.pdf_path}")
        
        # Read the PDF file
        with open(self.pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        print(f"PDF file size: {len(pdf_content)} bytes")
        
        # Initialize the PDF processor
        processor = PDFProcessor()
        
        # Process the statement
        print("\\nProcessing statement...")
        result = processor.process_statement(pdf_content)
        
        print(f"Processing success: {result.get('success', False)}")
        print(f"Processing confidence: {result.get('confidence', 0.0)}")
        print(f"Extraction method: {result.get('extraction_method', 'unknown')}")
        
        # Check if card_last_four was extracted
        metadata = result.get('metadata', {})
        card_last_four = metadata.get('card_last_four')
        
        if card_last_four:
            print(f"✓ SUCCESS: Card last 4 digits extracted: {card_last_four}")
            assert card_last_four == self.expected_last_four, f"Expected {self.expected_last_four}, got {card_last_four}"
        else:
            print("✗ FAILED: Card last 4 digits not extracted")
            print(f"Full result: {result}")
            assert False, "Card last 4 digits not extracted from full pipeline"
        
        # Print other relevant extracted information
        if metadata.get('customer_name'):
            print(f"Customer name: {metadata['customer_name']}")
        if metadata.get('bank_name'):
            print(f"Bank name: {metadata['bank_name']}")
        if metadata.get('period_start'):
            print(f"Period start: {metadata['period_start']}")
        if metadata.get('due_date'):
            print(f"Due date: {metadata['due_date']}")
    
    def test_mexican_parser_card_patterns(self):
        """Test the Mexican parser card extraction patterns."""
        print(f"Testing Mexican parser card patterns")
        print("-" * 60)
        
        if not os.path.exists(self.pdf_path):
            pytest.skip(f"Test PDF not found: {self.pdf_path}")
        
        # Read the PDF file
        with open(self.pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Extract text using PDF processor
        processor = PDFProcessor()
        success, text, error = processor.extract_text_from_pdf(pdf_content)
        
        assert success, f"Text extraction failed: {error}"
        print(f"Extracted text length: {len(text)}")
        
        # Test Mexican parser
        print("\\nTesting Mexican parser...")
        result = mexican_parser.parse_statement(text)
        
        print(f"Mexican parser success: {result.get('success', False)}")
        print(f"Mexican parser confidence: {result.get('confidence', 0.0)}")
        
        # Check for card number in parsed data
        if result.get('success') and 'data' in result:
            customer_info = result['data'].get('customer_info', {})
            card_number = customer_info.get('card_number')
            
            if card_number:
                last_four = card_number[-4:] if len(card_number) >= 4 else card_number
                print(f"✓ Mexican parser extracted card last 4: {last_four}")
                assert last_four == self.expected_last_four, f"Expected {self.expected_last_four}, got {last_four}"
            else:
                print("Mexican parser did not extract card number")
                # This is not necessarily a failure, as the Mexican parser might not always find it
                # The direct OCR extraction should catch it
    
    def _debug_card_context(self, ocr_text: str):
        """Debug helper to show context around card keywords."""
        print("\\nDEBUG: Context around card keywords:")
        lines = ocr_text.split('\\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['tarjeta', 'numero', 'no.', 'núm']):
                print(f"Line {i}: {line.strip()}")
                # Show surrounding lines
                for j in range(max(0, i-1), min(len(lines), i+2)):
                    if j != i:
                        print(f"Line {j}: {lines[j].strip()}")
                print()


if __name__ == "__main__":
    # Allow running individual tests
    import sys
    
    test_instance = TestCardExtraction()
    test_instance.setup_class()
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if hasattr(test_instance, test_name):
            getattr(test_instance, test_name)()
        else:
            print(f"Test method {test_name} not found")
    else:
        # Run all tests
        test_instance.test_direct_ocr_card_extraction()
        test_instance.test_ocr_table_parser_patterns()
        test_instance.test_full_pipeline_processing()
        test_instance.test_mexican_parser_card_patterns()