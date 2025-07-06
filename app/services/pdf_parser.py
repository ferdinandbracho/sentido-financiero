"""
PDF Text Extraction and Statement Processing Service

This module handles PDF text extraction and coordinates between template-based
parsing (Mexican statements) and LLM fallback parsing for other formats.

Author: StatementSense
Created: June 2025
"""

import io

import pytesseract
from typing import Dict

import pdfplumber
from app.config import settings
from app.models.statement import ExtractionMethodEnum
from app.services.mexican_parser import mexican_parser
from app.services.table_extractor import table_extractor
from app.services.ocr_table_parser import ocr_table_parser

logger = settings.get_logger(__name__)


class PDFProcessor:
    """
    Handles PDF text extraction and coordinates statement parsing strategies.

    Strategy:
    1. Extract text from PDF
    2. Try Mexican template parsing first (95% success rate, $0 cost)
    3. Fall back to LLM parsing if template fails (5% cases, small cost)
    """

    def __init__(self):
        self.logger = logger

    def extract_text_from_pdf(
        self, pdf_content: bytes
    ) -> tuple[bool, str, str]:
        """Extract text content from PDF bytes using pdfplumber.

        Returns:
            tuple: (success, text_content, error_message)
        """
        try:
            if not pdf_content:
                return False, "", "PDF content is empty"

            self.logger.info(
                f"Starting PDF text extraction for {len(pdf_content)} bytes"
            )
            pdf_file = io.BytesIO(pdf_content)

            text_content = ""
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    self.logger.info(f"Opened PDF with {len(pdf.pages)} pages")

                    if not pdf.pages:
                        return False, "", "PDF has no pages"

                    for page_num, page in enumerate(pdf.pages):
                        try:
                            self.logger.debug(
                                f"Extracting text from page {page_num + 1}"
                            )
                            page_text = page.extract_text()
                            
                            if page_text:
                                self.logger.debug(
                                    f"Extracted {len(page_text)} characters from page {page_num + 1}"
                                )
                                text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                            else:
                                # Fallback: Enhanced table extraction + OCR
                                try:
                                    self.logger.debug(
                                        "No text layer found, trying enhanced table extraction"
                                    )
                                    
                                    # Try table extraction first
                                    table_results = table_extractor.extract_tables_from_pdf(
                                        pdf_content, page_num
                                    )
                                    
                                    
                                    table_text = ""
                                    if table_results:
                                        best_result = max(table_results, key=lambda x: x.confidence)
                                        
                                        if best_result.success and best_result.tables:
                                            self.logger.debug(
                                                f"Table extraction successful with {best_result.method.value}, confidence: {best_result.confidence:.2f}"
                                            )
                                            # Convert tables to text format
                                            for i, table in enumerate(best_result.tables):
                                                table_text += f"\n--- Table {i+1} ---\n"
                                                table_text += table.to_string(index=False)
                                                table_text += "\n"
                                    
                                    # Fallback to basic OCR if no tables found
                                    if not table_text:
                                        self.logger.debug(
                                            "No tables found, falling back to basic OCR"
                                        )
                                        pil_image = page.to_image(resolution=300).original
                                        ocr_text = pytesseract.image_to_string(
                                            pil_image, lang="spa+eng"
                                        )
                                        if ocr_text and ocr_text.strip():
                                            table_text = ocr_text
                                    
                                    if table_text and table_text.strip():
                                        self.logger.debug(
                                            f"Enhanced extraction retrieved {len(table_text)} characters from page {page_num + 1}"
                                        )
                                        text_content += (
                                            f"\n--- Page {page_num + 1} (Enhanced) ---\n{table_text}"
                                        )
                                    else:
                                        self.logger.warning(
                                            f"Enhanced extraction returned no text for page {page_num + 1}"
                                        )
                                except Exception as ocr_err:
                                    self.logger.error(
                                        f"Enhanced extraction failed for page {page_num + 1}: {ocr_err}",
                                        exc_info=True,
                                    )
                                self.logger.warning(
                                    f"No text extracted from page {page_num + 1}"
                                )

                        except Exception as e:
                            error_msg = f"Failed to extract text from page {page_num + 1}: {str(e)}"
                            self.logger.error(error_msg, exc_info=True)
                            continue
            except Exception as e:
                return False, "", f"Failed to open PDF: {str(e)}"

            if not text_content.strip():
                error_msg = "No text content could be extracted from any page of the PDF"
                self.logger.error(error_msg)
                return False, "", error_msg

            self.logger.info(
                f"Successfully extracted {len(text_content)} characters from PDF"
            )
            return True, text_content, ""

        except Exception as e:
            error_msg = f"PDF text extraction failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg

    def detect_statement_type(self, text: str) -> str:
        """Detect the type of statement to determine parsing strategy."""
        
        # Check for Mexican CONDUSEF format indicators based on official structure guide
        # These are the mandated sections that MUST appear in all Mexican credit card statements
        
        # Primary CONDUSEF indicators (high confidence)
        primary_condusef_indicators = [
            "TU PAGO REQUERIDO ESTE PERIODO",
            "DESGLOSE DE MOVIMIENTOS",
            "PAGO PARA NO GENERAR INTERESES",
            "CARGOS, ABONOS Y COMPRAS REGULARES",
            "RESUMEN DE CARGOS Y ABONOS DEL PERIODO",
            "NIVEL DE USO DE TU TARJETA",
            "MENSAJES IMPORTANTES",
            "INDICADORES DEL COSTO ANUAL"
        ]
        
        # Secondary indicators (Mexican banks + common terms)
        secondary_indicators = [
            "SANTANDER", "BBVA", "BANAMEX", "BANORTE", "INBURSA", "SCOTIABANK",
            "HSBC", "CITIBANAMEX", "BANCO AZTECA", "AFIRME",
            "TARJETA DE CREDITO", "TARJETA DE CRÉDITO", "ESTADO DE CUENTA",
            "FECHA DE CORTE", "PAGO MINIMO", "PAGO MÍNIMO",
            "LIMITE DE CREDITO", "LÍMITE DE CRÉDITO", "CREDITO DISPONIBLE",
            "CRÉDITO DISPONIBLE", "SALDO DEUDOR", "CONDUSEF"
        ]
        
        # Transaction table headers (specific CONDUSEF format)
        transaction_table_headers = [
            "COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES",
            "COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES",
            "CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)",
            "CARGOS NO RECONOCIDOS"
        ]
        
        # CONDUSEF structural patterns for image-based statements
        structural_patterns = [
            r"Página \d+ de \d+",  # Page numbering
            r"Fecha de corte",     # Cut-off date
            r"Fecha límite de pago", # Payment due date
            r"RFC\s*[A-Z]{4}\d{6}[A-Z0-9]{3}", # Mexican RFC pattern
            r"\d{4}-\d{4}-\d{4}-\d{4}", # Card number pattern
            r"\$\s*[\d,]+\.?\d*",  # Mexican peso amounts
        ]
        
        primary_score = 0
        secondary_score = 0
        transaction_score = 0
        structural_score = 0
        
        text_upper = text.upper()
        
        for indicator in primary_condusef_indicators:
            if indicator in text_upper:
                primary_score += 1
        
        for indicator in secondary_indicators:
            if indicator in text_upper:
                secondary_score += 1
        
        for indicator in transaction_table_headers:
            if indicator in text_upper:
                transaction_score += 1
        
        import re
        for pattern in structural_patterns:
            if re.search(pattern, text_upper):
                structural_score += 1
        
        # Scoring logic for CONDUSEF detection
        
        # High confidence: Has primary CONDUSEF indicators
        if primary_score >= 1:
            return "mexican_condusef"
        
        # Medium confidence: Multiple secondary indicators + transaction tables
        if secondary_score >= 2 and transaction_score >= 1:
            return "mexican_condusef"
        
        # Low confidence: Strong secondary indicators + structural patterns
        if secondary_score >= 3 and structural_score >= 2:
            return "mexican_condusef"
        
        # Special case: Contains Mexican bank name + basic credit card terms
        mexican_banks = ["SANTANDER", "BBVA", "BANAMEX", "BANORTE", "INBURSA", "SCOTIABANK", "HSBC", "CITIBANAMEX"]
        has_mexican_bank = any(bank in text_upper for bank in mexican_banks)
        has_credit_terms = any(term in text_upper for term in ["TARJETA", "CREDITO", "CRÉDITO", "ESTADO DE CUENTA"])
        
        if has_mexican_bank and has_credit_terms:
            return "mexican_condusef"

        # Show first 500 chars to help debug
        
        return "unknown"

    def process_mexican_statement(self, text: str) -> Dict:
        """Process statement using Mexican template parser."""
        
        self.logger.info("Processing statement with Mexican template parser")

        parser_result = mexican_parser.parse_statement(text)
        

        if parser_result["success"]:
            self.logger.info(
                f"Mexican template parsing successful with confidence {parser_result['confidence']:.2f}"
            )

            # Transform the nested data structure to match what the upload endpoint expects
            result = {
                "success": parser_result["success"],
                "confidence": parser_result["confidence"],
                "extraction_method": "mexican_template",
                "metadata": {},
                "transactions": [],
            }

            # Extract customer info
            if (
                "data" in parser_result
                and "customer_info" in parser_result["data"]
            ):
                customer_info = parser_result["data"]["customer_info"]
                result["metadata"].update(
                    {
                        "bank_name": customer_info.get("bank_name"),
                        "customer_name": customer_info.get("customer_name"),
                        "card_last_four": customer_info.get("card_number")[-4:]
                        if customer_info.get("card_number")
                        else None,
                    }
                )

            # Extract payment info
            if (
                "data" in parser_result
                and "payment_info" in parser_result["data"]
            ):
                payment_info = parser_result["data"]["payment_info"]
                result["metadata"].update(
                    {
                        "period_start": payment_info.get("period_start"),
                        "period_end": payment_info.get("period_end"),
                        "cut_date": payment_info.get("cut_date"),
                        "due_date": payment_info.get("due_date"),
                        "pay_no_interest": payment_info.get("pay_no_interest"),
                        "minimum_payment": payment_info.get("minimum_payment"),
                    }
                )

            # Extract balance info
            if (
                "data" in parser_result
                and "balance_info" in parser_result["data"]
            ):
                balance_info = parser_result["data"]["balance_info"]
                result["metadata"].update(
                    {
                        "previous_balance": balance_info.get(
                            "previous_balance"
                        ),
                        "total_charges": balance_info.get("total_charges"),
                        "total_payments": balance_info.get("total_payments"),
                        "credit_limit": balance_info.get("credit_limit"),
                        "available_credit": balance_info.get(
                            "available_credit"
                        ),
                        "total_balance": balance_info.get("total_balance"),
                    }
                )

            # Extract transactions
            if (
                "data" in parser_result
                and "transactions" in parser_result["data"]
            ):
                for tx in parser_result["data"]["transactions"]:
                    transaction = {
                        "date": tx.get("operation_date"),
                        "charge_date": tx.get("charge_date"),
                        "description": tx.get("description", ""),
                        "amount": tx.get("amount"),
                        "type": "DEBIT"
                        if tx.get("transaction_type") == "DEBIT"
                        else "CREDIT",
                        "category": tx.get("category", "otros"),
                        "original_category": tx.get("category"),
                        "confidence": parser_result["confidence"],
                    }
                    result["transactions"].append(transaction)
        else:
            self.logger.warning(
                f"Mexican template parsing failed: {parser_result.get('error', 'Unknown error')}"
            )
            result = parser_result

        return result

    def process_llm_fallback(self, text: str) -> Dict:
        """Process statement using LLM as fallback (not implemented yet)."""
        self.logger.info("LLM fallback processing not yet implemented")

        return {
            "success": False,
            "error": "LLM fallback parsing not yet implemented",
            "confidence": 0.0,
            "extraction_method": "llm_fallback",
            "metadata": {},
            "transactions": [],
        }

    def process_statement(self, pdf_content: bytes, filename: str = None) -> Dict:
        """Process a statement PDF and extract structured data.

        Args:
            pdf_content: Raw PDF bytes
            filename: Original filename for fallback period extraction

        Returns:
            Dict with parsed statement data and metadata
        """
        if not pdf_content:
            self.logger.error("PDF content is empty")
            return {
                "success": False,
                "confidence": 0.0,
                "extraction_method": ExtractionMethodEnum.TEXT_EXTRACTION_FAILED,
                "error": "PDF content is empty",
                "raw_text": "",
            }

        self.logger.info(
            f"Starting statement processing for {len(pdf_content)} bytes"
        )

        try:
            # Step 1: Extract text from PDF
            success, text, error = self.extract_text_from_pdf(pdf_content)

            if not success:
                self.logger.error(f"Text extraction failed: {error}")
                return {
                    "success": False,
                    "confidence": 0.0,
                    "extraction_method": ExtractionMethodEnum.TEXT_EXTRACTION_FAILED,
                    "error": error,
                    "raw_text": text,  # For consistency
                }

            self.logger.debug(f"Extracted text length: {len(text)} characters")

            # Step 2: Detect statement type
            statement_type = self.detect_statement_type(text)
            self.logger.info(f"Detected statement type: {statement_type}")

            # Step 3: Process based on statement type
            if statement_type == "mexican_condusef":
                # Try Mexican template parsing
                result = self.process_mexican_statement(text)
                self.logger.info(
                    f"Mexican parser result: {result['success']} with confidence {result['confidence']:.2f}"
                )
                
                # Always try direct OCR extraction for card number from page 2 if not found or None
                card_last_four = result.get("metadata", {}).get("card_last_four") if result.get("metadata") else None
                if (card_last_four is None or not card_last_four):
                    self.logger.info("Attempting direct OCR card extraction from page 2")
                    try:
                        # Direct OCR extraction from page 2
                        import pytesseract
                        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                            if len(pdf.pages) > 1:  # Ensure page 2 exists
                                page = pdf.pages[1]  # Page 2 (0-indexed)
                                pil_image = page.to_image(resolution=300).original
                                ocr_text = pytesseract.image_to_string(
                                    pil_image,
                                    lang='spa+eng',
                                    config='--psm 6'
                                )
                                
                                # Extract card number using our proven pattern
                                import re
                                pattern = r'[Nn][úu]?mero de tarjeta[\s:]*(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})'
                                match = re.search(pattern, ocr_text, re.IGNORECASE)
                                
                                if match:
                                    card_number = match.group(1).replace(" ", "").replace("-", "")
                                    if len(card_number) == 16:
                                        extracted_last_four = card_number[-4:]
                                        self.logger.info(f"Direct OCR extracted card last 4: {extracted_last_four}")
                                        
                                        # Update result metadata
                                        if "metadata" not in result:
                                            result["metadata"] = {}
                                        result["metadata"]["card_last_four"] = extracted_last_four
                                    else:
                                        self.logger.warning(f"Invalid card number length: {len(card_number)}")
                                else:
                                    self.logger.warning("Direct OCR could not find card number pattern")
                            else:
                                self.logger.warning("PDF does not have a second page for card extraction")
                    except Exception as e:
                        self.logger.warning(f"Direct OCR card extraction failed: {e}")

                # Store any card number we extracted via direct OCR to preserve it
                extracted_card_last_four = result.get("metadata", {}).get("card_last_four")
                
                # If Mexican parsing failed or has low confidence, try enhanced table extraction
                if not result["success"] or result["confidence"] < 0.5:
                    self.logger.info(
                        "Mexican parsing failed or has low confidence, trying enhanced table extraction"
                    )
                    
                    # First try OCR header extraction for card numbers and basic info
                    try:
                        self.logger.info("Attempting OCR header extraction for card information")
                        
                        # Extract tables from PDF first (specifically for header info)
                        header_tables_result = table_extractor.extract_tables_from_pdf(pdf_content, 1)  # Page 2 where card info is
                        
                        if header_tables_result and header_tables_result.success:
                            # Parse tables for header info using OCR parser
                            ocr_result = ocr_table_parser.parse_tables(header_tables_result.tables)
                            
                            if ocr_result and hasattr(ocr_result, 'card_last_four') and ocr_result.card_last_four:
                                self.logger.info(f"OCR extracted card last 4: {ocr_result.card_last_four}")
                                # Update result metadata with OCR-extracted info
                                if "metadata" not in result:
                                    result["metadata"] = {}
                                result["metadata"]["card_last_four"] = ocr_result.card_last_four
                                if hasattr(ocr_result, 'customer_name') and ocr_result.customer_name:
                                    result["metadata"]["customer_name"] = ocr_result.customer_name
                            else:
                                self.logger.warning("OCR header extraction did not find card information")
                        else:
                            self.logger.warning("Failed to extract tables for OCR header parsing")
                    except Exception as e:
                        self.logger.warning(f"OCR header extraction failed: {e}")
                    
                    # Try direct table extraction for transactions
                    table_result = self.extract_transaction_tables(pdf_content)
                    
                    if table_result["success"]:
                        
                        self.logger.info(
                            f"Table extraction successful, re-trying Mexican parser with enhanced text"
                        )
                        # Re-try Mexican parser with enhanced text
                        enhanced_result = self.process_mexican_statement(table_result["extracted_text"])
                        
                        
                        if enhanced_result["success"]:
                            self.logger.info(
                                f"Enhanced Mexican parser successful with confidence {enhanced_result['confidence']:.2f}"
                            )
                            enhanced_result["raw_text"] = text
                            enhanced_result["extraction_method"] = "mexican_template"
                            
                            # Restore direct OCR extracted card number if it was found and current result doesn't have it
                            if (extracted_card_last_four and 
                                (not enhanced_result.get("metadata", {}).get("card_last_four"))):
                                self.logger.info(f"Restoring direct OCR card last 4: {extracted_card_last_four}")
                                if "metadata" not in enhanced_result:
                                    enhanced_result["metadata"] = {}
                                enhanced_result["metadata"]["card_last_four"] = extracted_card_last_four
                            
                            return enhanced_result
                        else:
                            # If Mexican parser still fails, try OCR table parser
                            ocr_result = self._process_with_ocr_parser(table_result["tables"], filename)
                            
                            if ocr_result["success"]:
                                ocr_result["raw_text"] = text
                                ocr_result["extraction_method"] = "mexican_template"
                                
                                # Restore direct OCR extracted card number if it was found and current result doesn't have it
                                if (extracted_card_last_four and 
                                    (not ocr_result.get("metadata", {}).get("card_last_four"))):
                                    self.logger.info(f"Restoring direct OCR card last 4: {extracted_card_last_four}")
                                    if "metadata" not in ocr_result:
                                        ocr_result["metadata"] = {}
                                    ocr_result["metadata"]["card_last_four"] = extracted_card_last_four
                                
                                return ocr_result
                    
                    # If table extraction also failed, try LLM fallback
                    self.logger.info(
                        "Table extraction failed, trying LLM fallback"
                    )
                    result = self.process_llm_fallback(text)
                    # Add raw text to result
                    result["raw_text"] = text
                    return result

                # Add raw text to result
                result["raw_text"] = text
                return result
            else:
                # Unknown statement type, try enhanced table extraction first, then LLM fallback
                self.logger.info(
                    f"Unknown statement type: {statement_type}, trying enhanced table extraction before LLM fallback"
                )
                
                # Try direct table extraction to see if we can extract Mexican-like data
                table_result = self.extract_transaction_tables(pdf_content)
                
                if table_result["success"]:
                    # Try Mexican parser on enhanced text
                    enhanced_result = self.process_mexican_statement(table_result["extracted_text"])
                    
                    if enhanced_result["success"]:
                        enhanced_result["raw_text"] = text
                        enhanced_result["extraction_method"] = "mexican_template"
                        return enhanced_result
                    else:
                        # Try OCR table parser
                        ocr_result = self._process_with_ocr_parser(table_result["tables"], filename)
                        
                        if ocr_result["success"]:
                            ocr_result["raw_text"] = text
                            ocr_result["extraction_method"] = "mexican_template"
                            return ocr_result
                        else:
                            pass
                
                # If table extraction failed or Mexican parser didn't work, use LLM fallback
                result = self.process_llm_fallback(text)
                # Add raw text to result
                result["raw_text"] = text
                return result

        except Exception as e:
            self.logger.error(
                f"Unexpected error processing statement: {str(e)}",
                exc_info=True,
            )
            return {
                "success": False,
                "confidence": 0.0,
                "extraction_method": ExtractionMethodEnum.TEXT_EXTRACTION_FAILED,
                "error": f"Unexpected error: {str(e)}",
                "raw_text": "",
            }

    def validate_pdf(self, pdf_content: bytes) -> bool:
        """Validate that the uploaded file is a proper PDF."""
        try:
            pdf_file = io.BytesIO(pdf_content)

            with pdfplumber.open(pdf_file) as pdf:
                # Check if PDF has pages
                if len(pdf.pages) == 0:
                    return False

                # Try to read first page to ensure it's not corrupted
                first_page = pdf.pages[0]
                first_page.extract_text()

            return True

        except Exception as e:
            self.logger.warning(f"PDF validation failed: {e}")
            return False

    def get_pdf_metadata(self, pdf_content: bytes) -> Dict:
        """Extract metadata from PDF for logging and tracking."""
        try:
            pdf_file = io.BytesIO(pdf_content)

            metadata = {}
            with pdfplumber.open(pdf_file) as pdf:
                metadata = {
                    "page_count": len(pdf.pages),
                    "file_size": len(pdf_content),
                }

                # Extract PDF metadata if available
                if hasattr(pdf, "metadata") and pdf.metadata:
                    metadata.update(
                        {
                            "title": pdf.metadata.get("Title"),
                            "author": pdf.metadata.get("Author"),
                            "subject": pdf.metadata.get("Subject"),
                            "creator": pdf.metadata.get("Creator"),
                            "producer": pdf.metadata.get("Producer"),
                            "creation_date": pdf.metadata.get("CreationDate"),
                            "modification_date": pdf.metadata.get("ModDate"),
                        }
                    )

            return metadata

        except Exception as e:
            self.logger.warning(f"Failed to extract PDF metadata: {e}")
            return {"error": str(e)}
    
    def extract_transaction_tables(self, pdf_content: bytes) -> Dict:
        """
        Extract transaction tables directly from PDF using enhanced methods.
        
        This method specifically targets transaction tables for statements
        that may not have proper text layers.
        """
        try:
            self.logger.info("Starting direct table extraction for transactions")
            
            # Use table extractor to find transaction tables
            transaction_tables = table_extractor.find_transaction_tables(pdf_content)
            
            
            if not transaction_tables:
                self.logger.warning("No transaction tables found")
                return {
                    "success": False,
                    "error": "No transaction tables found in PDF",
                    "tables": [],
                    "extraction_method": "table_extraction_failed"
                }
            
            # Convert tables to text format for Mexican parser
            combined_text = ""
            for i, table in enumerate(transaction_tables):
                self.logger.debug(f"Processing table {i+1} with {len(table)} rows")
                
                # Add section header for Mexican parser recognition
                combined_text += f"\n--- DESGLOSE DE MOVIMIENTOS ---\n"
                combined_text += table.to_string(index=False)
                combined_text += "\n"
            
            self.logger.info(f"Successfully extracted {len(transaction_tables)} transaction tables")
            
            return {
                "success": True,
                "extracted_text": combined_text,
                "tables": transaction_tables,
                "extraction_method": "enhanced_table_extraction"
            }
            
        except Exception as e:
            self.logger.error(f"Direct table extraction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tables": [],
                "extraction_method": "table_extraction_failed"
            }
    
    def _process_with_ocr_parser(self, tables: list, filename: str = None) -> Dict:
        """
        Process extracted tables using the OCR table parser.
        
        Args:
            tables: List of pandas DataFrames from table extraction
            
        Returns:
            Dict with parsed statement data
        """
        try:
            
            if not tables:
                return {
                    "success": False,
                    "error": "No tables provided for OCR parsing",
                    "confidence": 0.0,
                    "extraction_method": "ocr_table_parser",
                    "metadata": {},
                    "transactions": [],
                }
            
            # Parse tables using OCR parser
            parsed_statement = ocr_table_parser.parse_tables(tables, filename)
            
            # Convert to Mexican parser format
            result = ocr_table_parser.to_mexican_parser_format(parsed_statement)
            
            
            return result
            
        except Exception as e:
            self.logger.error(f"OCR table parser failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"OCR parsing failed: {str(e)}",
                "confidence": 0.0,
                "extraction_method": "ocr_table_parser",
                "metadata": {},
                "transactions": [],
            }


# Create singleton instance for easy import
pdf_processor = PDFProcessor()
