# Service Tests

This directory contains tests for the StatementSense service modules.

## Card Extraction Tests

The `test_card_extraction.py` module contains comprehensive tests for card number extraction functionality:

### Test Methods

1. **`test_direct_ocr_card_extraction`** - Tests direct OCR extraction from page 2 of PDF statements
2. **`test_ocr_table_parser_patterns`** - Tests the OCR table parser card extraction patterns
3. **`test_full_pipeline_processing`** - Tests the complete PDF processing pipeline
4. **`test_mexican_parser_card_patterns`** - Tests the Mexican parser card extraction patterns

### Running Tests

#### Run all card extraction tests:
```bash
cd /Users/ferdinandbracho/code/projects/statement-sense
python tests/services/test_card_extraction.py
```

#### Run individual test methods:
```bash
python tests/services/test_card_extraction.py test_direct_ocr_card_extraction
python tests/services/test_card_extraction.py test_full_pipeline_processing
```

#### Run with pytest (recommended):
```bash
pytest tests/services/test_card_extraction.py -v
pytest tests/services/test_card_extraction.py::TestCardExtraction::test_full_pipeline_processing -v
```

### Test Requirements

- The test PDF file should be available at: `/Users/ferdinandbracho/code/projects/statement-sense/.windsurf/Estado de cuenta mayo 2025.pdf`
- All service dependencies should be installed (pytesseract, pdfplumber, etc.)
- The expected card last 4 digits for the test PDF is "5262"

### Test Coverage

These tests cover:
- Direct OCR text extraction and pattern matching
- Table-based extraction methods
- Full processing pipeline including fallback mechanisms
- Mexican template parser integration
- Error handling and debugging capabilities

The tests are designed to be resilient and provide detailed debugging output when card extraction fails.