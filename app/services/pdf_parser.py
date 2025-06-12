"""
PDF Text Extraction and Statement Processing Service

This module handles PDF text extraction and coordinates between template-based
parsing (Mexican statements) and LLM fallback parsing for other formats.

Author: StatementSense
Created: June 2025
"""
import io
from typing import Dict

import pdfplumber
from app.config import settings
from app.models.statement import ExtractionMethodEnum
from app.services.mexican_parser import mexican_parser

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

    def extract_text_from_pdf(self, pdf_content: bytes) -> tuple[bool, str, str]:
        """Extract text content from PDF bytes using pdfplumber.
        
        Returns:
            tuple: (success, text_content, error_message)
        """
        try:
            if not pdf_content:
                return False, "", "PDF content is empty"
                
            self.logger.info(f"Starting PDF text extraction for {len(pdf_content)} bytes")
            pdf_file = io.BytesIO(pdf_content)

            text_content = ""
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    self.logger.info(f"Opened PDF with {len(pdf.pages)} pages")
                    
                    if not pdf.pages:
                        return False, "", "PDF has no pages"
                    
                    for page_num, page in enumerate(pdf.pages):
                        try:
                            self.logger.debug(f"Extracting text from page {page_num + 1}")
                            page_text = page.extract_text()
                            
                            if page_text:
                                self.logger.debug(f"Extracted {len(page_text)} characters from page {page_num + 1}")
                                text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                            else:
                                self.logger.warning(f"No text extracted from page {page_num + 1}")
                                
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

            self.logger.info(f"Successfully extracted {len(text_content)} characters from PDF")
            return True, text_content, ""

        except Exception as e:
            error_msg = f"PDF text extraction failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg

    def detect_statement_type(self, text: str) -> str:
        """Detect the type of statement to determine parsing strategy."""
        # Check for Mexican CONDUSEF format indicators
        mexican_indicators = [
            "TU PAGO REQUERIDO ESTE PERIODO",
            "DESGLOSE DE MOVIMIENTOS",
            "CONDUSEF",
            "Banco de México",
        ]

        for indicator in mexican_indicators:
            if indicator in text:
                return "mexican_condusef"

        # Check for other specific formats (future expansion)
        if "AMERICAN EXPRESS" in text.upper():
            return "amex_international"
        elif "VISA" in text.upper() or "MASTERCARD" in text.upper():
            return "international_card"

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
                "transactions": []
            }
            
            # Extract customer info
            if "data" in parser_result and "customer_info" in parser_result["data"]:
                customer_info = parser_result["data"]["customer_info"]
                result["metadata"].update({
                    "bank_name": customer_info.get("bank_name"),
                    "customer_name": customer_info.get("customer_name"),
                    "card_last_four": customer_info.get("card_number")[-4:] if customer_info.get("card_number") else None
                })
            
            # Extract payment info
            if "data" in parser_result and "payment_info" in parser_result["data"]:
                payment_info = parser_result["data"]["payment_info"]
                result["metadata"].update({
                    "period_start": payment_info.get("period_start"),
                    "period_end": payment_info.get("period_end"),
                    "cut_date": payment_info.get("cut_date"),
                    "due_date": payment_info.get("due_date"),
                    "pay_no_interest": payment_info.get("pay_no_interest"),
                    "minimum_payment": payment_info.get("minimum_payment")
                })
            
            # Extract balance info
            if "data" in parser_result and "balance_info" in parser_result["data"]:
                balance_info = parser_result["data"]["balance_info"]
                result["metadata"].update({
                    "previous_balance": balance_info.get("previous_balance"),
                    "total_charges": balance_info.get("total_charges"),
                    "total_payments": balance_info.get("total_payments"),
                    "credit_limit": balance_info.get("credit_limit"),
                    "available_credit": balance_info.get("available_credit"),
                    "total_balance": balance_info.get("total_balance")
                })
            
            # Extract transactions
            if "data" in parser_result and "transactions" in parser_result["data"]:
                for tx in parser_result["data"]["transactions"]:
                    transaction = {
                        "date": tx.get("operation_date"),
                        "charge_date": tx.get("charge_date"),
                        "description": tx.get("description", ""),
                        "amount": tx.get("amount"),
                        "type": "DEBIT" if tx.get("transaction_type") == "DEBIT" else "CREDIT",
                        "category": tx.get("category", "otros"),
                        "original_category": tx.get("category"),
                        "confidence": parser_result["confidence"]
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
            "transactions": []
        }

    def process_statement(self, pdf_content: bytes) -> Dict:
        """Process a statement PDF and extract structured data.

        Args:
            pdf_content: Raw PDF bytes

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
                "raw_text": ""
            }
            
        self.logger.info(f"Starting statement processing for {len(pdf_content)} bytes")

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
                    "raw_text": text  # This will be empty string but we include it for consistency
                }
                
            self.logger.debug(f"Extracted text length: {len(text)} characters")
            
            # Step 2: Detect statement type
            statement_type = self.detect_statement_type(text)
            self.logger.info(f"Detected statement type: {statement_type}")
            
            # Step 3: Process based on statement type
            if statement_type == "mexican_condusef":
                # Try Mexican template parsing
                result = self.process_mexican_statement(text)
                self.logger.info(f"Mexican parser result: {result['success']} with confidence {result['confidence']:.2f}")
                
                # If Mexican parsing failed or has low confidence, try LLM fallback
                if not result["success"] or result["confidence"] < 0.5:
                    self.logger.info("Mexican parsing failed or has low confidence, trying LLM fallback")
                    result = self.process_llm_fallback(text)
                    # Add raw text to result
                    result["raw_text"] = text
                    return result
                
                # Add raw text to result
                result["raw_text"] = text
                return result
            else:
                # Unknown statement type, use LLM fallback
                self.logger.info(f"Unknown statement type: {statement_type}, using LLM fallback")
                result = self.process_llm_fallback(text)
                # Add raw text to result
                result["raw_text"] = text
                return result
                
        except Exception as e:
            self.logger.error(f"Unexpected error processing statement: {str(e)}", exc_info=True)
            return {
                "success": False,
                "confidence": 0.0,
                "extraction_method": ExtractionMethodEnum.TEXT_EXTRACTION_FAILED,
                "error": f"Unexpected error: {str(e)}",
                "raw_text": ""
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


# Create singleton instance for easy import
pdf_processor = PDFProcessor()
