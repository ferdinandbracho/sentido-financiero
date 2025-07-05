"""
Enhanced Table Extraction Service for PDF Statements

This module provides multiple strategies for extracting tabular data from PDF statements,
with special focus on Mexican credit card statements' "desglose de movimientos" tables.

Author: StatementSense
Created: July 2025
"""

import io
import cv2
import numpy as np
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False

from app.config import settings

logger = settings.get_logger(__name__)


class TableExtractionMethod(Enum):
    """Available table extraction methods."""
    PDFPLUMBER = "pdfplumber"
    CAMELOT_LATTICE = "camelot_lattice"
    CAMELOT_STREAM = "camelot_stream"
    TABULA = "tabula"
    ENHANCED_OCR = "enhanced_ocr"


@dataclass
class TableExtractionResult:
    """Result of table extraction attempt."""
    success: bool
    method: TableExtractionMethod
    tables: List[pd.DataFrame]
    confidence: float
    error_message: Optional[str] = None
    raw_data: Optional[Any] = None


class TableExtractor:
    """
    Enhanced table extraction service with multiple fallback strategies.
    
    Strategies (in order of preference):
    1. pdfplumber - Fast, good for simple tables
    2. Camelot (lattice) - Best for bordered tables
    3. Camelot (stream) - Good for stream-based tables
    4. Tabula - Java-based, reliable fallback
    5. Enhanced OCR - Last resort with image preprocessing
    """
    
    def __init__(self):
        self.logger = logger
        
    def extract_tables_from_pdf(self, pdf_content: bytes, page_number: int = 0) -> List[TableExtractionResult]:
        """
        Extract tables from PDF using multiple strategies.
        
        Args:
            pdf_content: Raw PDF bytes
            page_number: Page to extract from (0-indexed)
            
        Returns:
            List of extraction results from different methods
        """
        print(f"🔍 DEBUG: Starting table extraction for page {page_number}")
        results = []
        
        # Strategy 1: pdfplumber
        try:
            print(f"🔍 DEBUG: Trying pdfplumber extraction")
            result = self._extract_with_pdfplumber(pdf_content, page_number)
            results.append(result)
            print(f"🔍 DEBUG: pdfplumber result - Success: {result.success}, Confidence: {result.confidence:.2f}, Tables: {len(result.tables)}")
            if result.success and result.confidence > 0.7:
                print(f"🔍 DEBUG: High confidence with pdfplumber, returning early")
                self.logger.info(f"High confidence extraction with pdfplumber: {result.confidence:.2f}")
                return results
        except Exception as e:
            print(f"🔍 DEBUG: pdfplumber failed: {e}")
            self.logger.warning(f"pdfplumber extraction failed: {e}")
            
        # Strategy 2: Camelot (lattice)
        if CAMELOT_AVAILABLE:
            try:
                print(f"🔍 DEBUG: Trying Camelot lattice extraction")
                result = self._extract_with_camelot(pdf_content, page_number, flavor='lattice')
                results.append(result)
                print(f"🔍 DEBUG: Camelot lattice result - Success: {result.success}, Confidence: {result.confidence:.2f}, Tables: {len(result.tables)}")
                if result.success and result.confidence > 0.7:
                    print(f"🔍 DEBUG: High confidence with Camelot lattice, returning early")
                    self.logger.info(f"High confidence extraction with Camelot lattice: {result.confidence:.2f}")
                    return results
            except Exception as e:
                print(f"🔍 DEBUG: Camelot lattice failed: {e}")
                self.logger.warning(f"Camelot lattice extraction failed: {e}")
                
        # Strategy 3: Camelot (stream)
        if CAMELOT_AVAILABLE:
            try:
                print(f"🔍 DEBUG: Trying Camelot stream extraction")
                result = self._extract_with_camelot(pdf_content, page_number, flavor='stream')
                results.append(result)
                print(f"🔍 DEBUG: Camelot stream result - Success: {result.success}, Confidence: {result.confidence:.2f}, Tables: {len(result.tables)}")
                if result.success and result.confidence > 0.7:
                    print(f"🔍 DEBUG: High confidence with Camelot stream, returning early")
                    self.logger.info(f"High confidence extraction with Camelot stream: {result.confidence:.2f}")
                    return results
            except Exception as e:
                print(f"🔍 DEBUG: Camelot stream failed: {e}")
                self.logger.warning(f"Camelot stream extraction failed: {e}")
                
        # Strategy 4: Tabula
        if TABULA_AVAILABLE:
            try:
                print(f"🔍 DEBUG: Trying Tabula extraction")
                result = self._extract_with_tabula(pdf_content, page_number)
                results.append(result)
                print(f"🔍 DEBUG: Tabula result - Success: {result.success}, Confidence: {result.confidence:.2f}, Tables: {len(result.tables)}")
                if result.success and result.confidence > 0.7:
                    print(f"🔍 DEBUG: High confidence with Tabula, returning early")
                    self.logger.info(f"High confidence extraction with Tabula: {result.confidence:.2f}")
                    return results
            except Exception as e:
                print(f"🔍 DEBUG: Tabula failed: {e}")
                self.logger.warning(f"Tabula extraction failed: {e}")
                
        # Strategy 5: Enhanced OCR (last resort)
        try:
            print(f"🔍 DEBUG: Trying Enhanced OCR extraction")
            result = self._extract_with_enhanced_ocr(pdf_content, page_number)
            results.append(result)
            print(f"🔍 DEBUG: Enhanced OCR result - Success: {result.success}, Confidence: {result.confidence:.2f}, Tables: {len(result.tables)}")
        except Exception as e:
            print(f"🔍 DEBUG: Enhanced OCR failed: {e}")
            self.logger.warning(f"Enhanced OCR extraction failed: {e}")
            
        print(f"🔍 DEBUG: All extraction methods completed, returning {len(results)} results")
        return results
    
    def _extract_with_pdfplumber(self, pdf_content: bytes, page_number: int) -> TableExtractionResult:
        """Extract tables using pdfplumber."""
        pdf_file = io.BytesIO(pdf_content)
        tables = []
        
        with pdfplumber.open(pdf_file) as pdf:
            if page_number >= len(pdf.pages):
                return TableExtractionResult(
                    success=False,
                    method=TableExtractionMethod.PDFPLUMBER,
                    tables=[],
                    confidence=0.0,
                    error_message=f"Page {page_number} not found"
                )
                
            page = pdf.pages[page_number]
            extracted_tables = page.extract_tables()
            
            for table_data in extracted_tables:
                if table_data:
                    # Convert to DataFrame
                    df = pd.DataFrame(table_data[1:], columns=table_data[0])
                    # Clean empty rows/columns
                    df = df.dropna(how='all').dropna(axis=1, how='all')
                    if not df.empty:
                        tables.append(df)
                        
        confidence = 0.8 if tables else 0.0
        
        return TableExtractionResult(
            success=bool(tables),
            method=TableExtractionMethod.PDFPLUMBER,
            tables=tables,
            confidence=confidence,
            raw_data=extracted_tables
        )
    
    def _extract_with_camelot(self, pdf_content: bytes, page_number: int, flavor: str) -> TableExtractionResult:
        """Extract tables using Camelot."""
        if not CAMELOT_AVAILABLE:
            return TableExtractionResult(
                success=False,
                method=TableExtractionMethod.CAMELOT_LATTICE if flavor == 'lattice' else TableExtractionMethod.CAMELOT_STREAM,
                tables=[],
                confidence=0.0,
                error_message="Camelot not available"
            )
            
        # Save PDF to temporary file (Camelot requires file path)
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file_path = tmp_file.name
            
        try:
            # Extract tables
            camelot_tables = camelot.read_pdf(
                tmp_file_path,
                pages=str(page_number + 1),  # Camelot uses 1-based indexing
                flavor=flavor
            )
            
            tables = []
            total_accuracy = 0.0
            
            for table in camelot_tables:
                df = table.df
                # Clean empty rows/columns
                df = df.dropna(how='all').dropna(axis=1, how='all')
                if not df.empty:
                    tables.append(df)
                    total_accuracy += table.accuracy
                    
            confidence = total_accuracy / len(camelot_tables) / 100.0 if camelot_tables else 0.0
            
            return TableExtractionResult(
                success=bool(tables),
                method=TableExtractionMethod.CAMELOT_LATTICE if flavor == 'lattice' else TableExtractionMethod.CAMELOT_STREAM,
                tables=tables,
                confidence=confidence,
                raw_data=camelot_tables
            )
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
    
    def _extract_with_tabula(self, pdf_content: bytes, page_number: int) -> TableExtractionResult:
        """Extract tables using Tabula."""
        if not TABULA_AVAILABLE:
            return TableExtractionResult(
                success=False,
                method=TableExtractionMethod.TABULA,
                tables=[],
                confidence=0.0,
                error_message="Tabula not available"
            )
            
        # Save PDF to temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file_path = tmp_file.name
            
        try:
            # Extract tables
            tabula_tables = tabula.read_pdf(
                tmp_file_path,
                pages=page_number + 1,  # Tabula uses 1-based indexing
                multiple_tables=True,
                pandas_options={'header': 0}
            )
            
            tables = []
            for df in tabula_tables:
                # Clean empty rows/columns
                df = df.dropna(how='all').dropna(axis=1, how='all')
                if not df.empty:
                    tables.append(df)
                    
            confidence = 0.7 if tables else 0.0
            
            return TableExtractionResult(
                success=bool(tables),
                method=TableExtractionMethod.TABULA,
                tables=tables,
                confidence=confidence,
                raw_data=tabula_tables
            )
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
    
    def _extract_with_enhanced_ocr(self, pdf_content: bytes, page_number: int) -> TableExtractionResult:
        """Extract tables using enhanced OCR with preprocessing."""
        pdf_file = io.BytesIO(pdf_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            if page_number >= len(pdf.pages):
                return TableExtractionResult(
                    success=False,
                    method=TableExtractionMethod.ENHANCED_OCR,
                    tables=[],
                    confidence=0.0,
                    error_message=f"Page {page_number} not found"
                )
                
            page = pdf.pages[page_number]
            
            # Convert page to high-resolution image
            pil_image = page.to_image(resolution=300).original
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image_for_ocr(pil_image)
            
            # Try structured OCR (table detection)
            try:
                # Use pytesseract with table-specific PSM
                ocr_data = pytesseract.image_to_data(
                    processed_image,
                    lang='spa+eng',
                    output_type=pytesseract.Output.DICT,
                    config='--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .-+$,'
                )
                
                # Reconstruct table structure from OCR data
                tables = self._reconstruct_table_from_ocr(ocr_data)
                
                confidence = 0.5 if tables else 0.0
                
                return TableExtractionResult(
                    success=bool(tables),
                    method=TableExtractionMethod.ENHANCED_OCR,
                    tables=tables,
                    confidence=confidence,
                    raw_data=ocr_data
                )
                
            except Exception as e:
                self.logger.error(f"Enhanced OCR failed: {e}")
                return TableExtractionResult(
                    success=False,
                    method=TableExtractionMethod.ENHANCED_OCR,
                    tables=[],
                    confidence=0.0,
                    error_message=str(e)
                )
    
    def _preprocess_image_for_ocr(self, pil_image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy for tables."""
        # Convert PIL to OpenCV format
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply morphological operations to enhance table lines
        kernel = np.ones((1, 1), np.uint8)
        
        # Enhance horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # Enhance vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Combine enhanced lines
        enhanced = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
        enhanced = cv2.addWeighted(gray, 0.7, enhanced, 0.3, 0.0)
        
        # Apply bilateral filter to reduce noise while preserving edges
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Adaptive thresholding for better text clarity
        threshold = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Convert back to PIL
        processed_image = Image.fromarray(threshold)
        
        return processed_image
    
    def _reconstruct_table_from_ocr(self, ocr_data: Dict) -> List[pd.DataFrame]:
        """Reconstruct table structure from OCR data."""
        # Extract text blocks with their positions
        text_blocks = []
        
        for i, text in enumerate(ocr_data['text']):
            if text.strip():  # Skip empty text
                text_blocks.append({
                    'text': text.strip(),
                    'left': ocr_data['left'][i],
                    'top': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i],
                    'conf': ocr_data['conf'][i]
                })
        
        if not text_blocks:
            return []
        
        # Group text blocks by row (similar Y coordinates)
        rows = []
        current_row = []
        row_threshold = 10  # Pixels tolerance for same row
        
        # Sort by Y coordinate (top)
        text_blocks.sort(key=lambda x: x['top'])
        
        for block in text_blocks:
            if not current_row:
                current_row = [block]
            else:
                # Check if block is in same row as previous blocks
                avg_top = sum(b['top'] for b in current_row) / len(current_row)
                if abs(block['top'] - avg_top) <= row_threshold:
                    current_row.append(block)
                else:
                    # Start new row
                    if current_row:
                        current_row.sort(key=lambda x: x['left'])  # Sort by X coordinate
                        rows.append(current_row)
                    current_row = [block]
        
        # Add last row
        if current_row:
            current_row.sort(key=lambda x: x['left'])
            rows.append(current_row)
        
        # Convert to DataFrame
        if rows:
            # Determine number of columns (max columns in any row)
            max_cols = max(len(row) for row in rows)
            
            # Create table data
            table_data = []
            for row in rows:
                row_data = [block['text'] for block in row]
                # Pad with empty strings if needed
                while len(row_data) < max_cols:
                    row_data.append('')
                table_data.append(row_data)
            
            if table_data:
                df = pd.DataFrame(table_data)
                # Clean empty rows/columns
                df = df.dropna(how='all').dropna(axis=1, how='all')
                if not df.empty:
                    return [df]
        
        return []
    
    def find_transaction_tables(self, pdf_content: bytes) -> List[pd.DataFrame]:
        """
        Find transaction tables specifically (Mexican statements).
        
        Looks for tables containing transaction-like data patterns.
        """
        print(f"🔍 DEBUG: Starting transaction table search")
        all_tables = []
        
        # Try extracting from each page
        pdf_file = io.BytesIO(pdf_content)
        with pdfplumber.open(pdf_file) as pdf:
            print(f"🔍 DEBUG: PDF has {len(pdf.pages)} pages")
            for page_num in range(len(pdf.pages)):
                print(f"🔍 DEBUG: Processing page {page_num + 1} for transaction tables")
                results = self.extract_tables_from_pdf(pdf_content, page_num)
                
                # Get best result for this page
                best_result = max(results, key=lambda x: x.confidence) if results else None
                
                if best_result and best_result.success:
                    print(f"🔍 DEBUG: Page {page_num + 1} - Found {len(best_result.tables)} tables, checking for transaction patterns")
                    # Filter for transaction-like tables
                    for i, table in enumerate(best_result.tables):
                        is_transaction = self._is_transaction_table(table)
                        print(f"🔍 DEBUG: Table {i+1} on page {page_num + 1} - Is transaction table: {is_transaction}")
                        if is_transaction:
                            print(f"🔍 DEBUG: Adding transaction table {i+1} from page {page_num + 1} ({len(table)} rows)")
                            all_tables.append(table)
                else:
                    print(f"🔍 DEBUG: Page {page_num + 1} - No successful extraction results")
                            
        print(f"🔍 DEBUG: Found {len(all_tables)} transaction tables total")
        return all_tables
    
    def _is_transaction_table(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame looks like a transaction table."""
        if df.empty:
            return False
            
        print(f"🔍 DEBUG: Checking table with {len(df)} rows x {len(df.columns)} columns")
        print(f"🔍 DEBUG: First 3 rows of table:\n{df.head(3).to_string(index=False)}")
        
        # For image-based PDFs, be more flexible with transaction detection
        # Look for larger tables that might contain transaction data
        if len(df) >= 10 and len(df.columns) >= 3:
            print(f"🔍 DEBUG: Large table detected ({len(df)} rows), likely contains transactions")
            return True
            
        # Look for date patterns in any column (not just first)
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD/MM/YYYY or DD-MM-YYYY
            r'\d{1,2}[-/]\w{3}[-/]\d{2,4}',    # DD-MMM-YYYY
            r'\d{1,2}-\w{3}-\d{4}',            # DD-MMM-YYYY (Mexican format)
            r'\w{3}-\d{1,2}',                  # MMM-DD
            r'\d{1,2}/\d{1,2}',                # MM/DD or DD/MM
        ]
        
        total_date_matches = 0
        total_cells = 0
        
        # Check all columns for date patterns
        import re
        for col_idx in range(min(len(df.columns), 5)):  # Check first 5 columns
            try:
                col_data = df.iloc[:, col_idx].astype(str)
                for pattern in date_patterns:
                    date_matches = sum(1 for text in col_data if re.search(pattern, text))
                    total_date_matches += date_matches
                total_cells += len(col_data)
            except:
                continue
        
        # Also look for monetary patterns (amounts)
        amount_patterns = [
            r'\$\s*[\d,]+\.?\d*',              # $1,234.56
            r'[\d,]+\.?\d*\s*\$',              # 1,234.56$
            r'[\d,]+\.\d{2}',                  # 1,234.56
        ]
        
        amount_matches = 0
        for col_idx in range(min(len(df.columns), 5)):
            try:
                col_data = df.iloc[:, col_idx].astype(str)
                for pattern in amount_patterns:
                    amount_matches += sum(1 for text in col_data if re.search(pattern, text))
            except:
                continue
        
        # Look for transaction-like keywords
        transaction_keywords = [
            'PAGO', 'COMPRA', 'RETIRO', 'DEPOSITO', 'TRANSFERENCIA',
            'RESTAURANTE', 'TIENDA', 'FARMACIA', 'GASOLINA', 'ATM',
            'VISA', 'MASTERCARD', 'DEBITO', 'CREDITO'
        ]
        
        keyword_matches = 0
        all_text = ' '.join(df.astype(str).values.flatten()).upper()
        for keyword in transaction_keywords:
            if keyword in all_text:
                keyword_matches += 1
        
        date_ratio = total_date_matches / max(total_cells, 1)
        has_amounts = amount_matches > 0
        has_keywords = keyword_matches > 0
        
        print(f"🔍 DEBUG: Date matches: {total_date_matches}/{total_cells} = {date_ratio:.2f}")
        print(f"🔍 DEBUG: Amount matches: {amount_matches}")
        print(f"🔍 DEBUG: Keyword matches: {keyword_matches}")
        
        # More relaxed criteria for image-based PDFs
        is_transaction = (
            (date_ratio > 0.1) or  # 10% date patterns
            has_amounts or         # Has monetary amounts
            has_keywords or        # Has transaction keywords
            (len(df) > 20 and len(df.columns) >= 4)  # Large table with multiple columns
        )
        
        print(f"🔍 DEBUG: Is transaction table: {is_transaction}")
        return is_transaction


# Create singleton instance
table_extractor = TableExtractor()