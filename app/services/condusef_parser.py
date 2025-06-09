import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pdfplumber

logger = logging.getLogger(__name__)

# Spanish month abbreviations to standard English for date parsing
SPANISH_MONTHS_SHORT = {
    'ENE': 'JAN', 'FEB': 'FEB', 'MAR': 'MAR', 'ABR': 'APR',
    'MAY': 'MAY', 'JUN': 'JUN', 'JUL': 'JUL', 'AGO': 'AUG',
    'SEP': 'SEP', 'OCT': 'OCT', 'NOV': 'NOV', 'DIC': 'DEC'
}

class CondusefParser:
    """
    Parses PDF bank statements based on the standardized CONDUSEF
    structure for Mexican credit card statements.
    """

    def __init__(self, ollama_llm_service=None):
        self.llm_service = ollama_llm_service
        # Regex patterns for key sections and data points based on CONDUSEF guide
        self.patterns = {
            # Section 2: Page Numbers
            "page_number": r"Página\s*(\d+)\s*de\s*(\d+)",
            # Section 4: Product Identification
            # Simplified, needs refinement for card_type
            "card_type": r"(Tarjeta Clásica|Tarjeta Oro|Tarjeta Platino|.+)",
            "account_number": r"(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})", # 16-digit
            "rfc": r"RFC:\s*([A-Z&Ñ]{3,4}\d{2}(?:0[1-9]|1[0-2])"
                   r"(?:0[1-9]|[12]\d|3[01])[A-Z\d]{2}[A\d])",
            # Section 5: Payment Required This Period
            "statement_period": r"Periodo:\s*(\d{2}-\w{3}-\d{4})\s*al\s*"
                                r"(\d{2}-\w{3}-\d{4})",
            "cutoff_date": r"Fecha de corte:\s*(\d{2}-\w{3}-\d{4})",
            "payment_due_date": r"Fecha límite de pago:\s*(\d{2}-\w{3}-\d{4})",
            "pay_to_avoid_interest": r"Pago para no generar intereses:\s*\$"
                                     r"([\d,]+\.\d{2})",
            "minimum_payment": r"Pago mínimo:\s*\$([\d,]+\.\d{2})",
            # Section 22: Transaction Details - Table Headers
            "no_interest_installments_header": 
                r"COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES",
            "interest_bearing_installments_header": 
                r"COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES",
            "regular_transactions_header": 
                r"CARGOS, ABONOS Y COMPRAS REGULARES \(NO A MESES\)",
        }

    def _normalize_date_spanish(self, date_str: str) -> str:
        """Converts Spanish month abbreviations in a date string to English."""
        if not date_str:
            return date_str
        for esp, eng in SPANISH_MONTHS_SHORT.items():
            date_str = date_str.upper().replace(esp, eng)
        return date_str

    def _parse_date(self, date_str: str, 
                      formats: List[str] = ["%d-%b-%Y", "%d/%m/%Y"]) -> Optional[datetime]:
        """Parses a date string, handling Spanish months."""
        if not date_str:
            return None
        normalized_date_str = self._normalize_date_spanish(date_str)
        for fmt in formats:
            try:
                return datetime.strptime(normalized_date_str, fmt)
            except ValueError:
                continue
        logger.warning(
            f"Could not parse date: {date_str} (normalized: {normalized_date_str})"
        )
        return None

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Converts a currency string (e.g., "$1,234.56") to a float."""
        if not amount_str:
            return None
        try:
            return float(amount_str.replace('$', '').replace(',', ''))
        except ValueError:
            logger.warning(f"Could not parse amount: {amount_str}")
            return None

    def classify_document_type(self, text: str) -> str:
        """Classifies if the document is a bank statement or other.

        Placeholder: Basic keyword check. Needs more robust LLM-based 
        classification.
        """
        keywords = [
            "estado de cuenta", "fecha de corte", 
            "pago mínimo", "movimientos"
        ]
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in keywords):
            # Further check for CONDUSEF specific section headers
            condusef_sections = [
                self.patterns["no_interest_installments_header"].lower(),
                self.patterns["interest_bearing_installments_header"].lower(),
                self.patterns["regular_transactions_header"].lower(),
                "resumen de cargos y abonos",
                "pago requerido este periodo"
            ]
            if any(section_header in text_lower 
                   for section_header in condusef_sections):
                return "credit_card_statement_condusef"
            return "bank_statement_other"
        return "other_document"

    def extract_primary_information(self, page_text: str) -> Dict[str, Any]:
        """Extracts primary information (Sections 1-12) from Page 1."""
        data = {}
        # Section 3: Mailing Data (Placeholder - complex, needs layout analysis or LLM)
        # Section 4: Product Identification
        account_match = re.search(self.patterns["account_number"], page_text)
        if account_match:
            data['account_number'] = account_match.group(1).replace(' ', '')
        
        rfc_match = re.search(self.patterns["rfc"], page_text, re.IGNORECASE)
        if rfc_match:
            data['rfc'] = rfc_match.group(1)

        # Section 5: Payment Required This Period
        period_match = re.search(self.patterns["statement_period"], page_text, re.IGNORECASE)
        if period_match:
            data['statement_period_start'] = self._parse_date(period_match.group(1))
            data['statement_period_end'] = self._parse_date(period_match.group(2))

        cutoff_match = re.search(self.patterns["cutoff_date"], page_text, re.IGNORECASE)
        if cutoff_match:
            data['cutoff_date'] = self._parse_date(cutoff_match.group(1))

        due_date_match = re.search(self.patterns["payment_due_date"], page_text, re.IGNORECASE)
        if due_date_match:
            data['payment_due_date'] = self._parse_date(due_date_match.group(1))

        avoid_interest_match = re.search(self.patterns["pay_to_avoid_interest"], page_text, re.IGNORECASE)
        if avoid_interest_match:
            data['pay_to_avoid_interest'] = self._parse_amount(
                avoid_interest_match.group(1)
            )

        min_payment_match = re.search(self.patterns["minimum_payment"], page_text, re.IGNORECASE)
        if min_payment_match:
            data['minimum_payment'] = self._parse_amount(min_payment_match.group(1))
        
        # Placeholder for other sections (1, 2, 6-12)
        # These often require more complex parsing or LLM assistance
        logger.info(f"Extracted primary info (first page): {data}")
        return data

    def _extract_transactions_from_table_text(
            self, table_text: str, transaction_type: str, 
            year_context: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extracts transactions from a block of text for a transaction table."""
        transactions = []
        lines = table_text.strip().split('\n')
        current_year = year_context if year_context else datetime.now().year

        # Regex patterns for transaction lines. These are highly dependent on table
        # structure and need to be robust. CONDUSEF provides column names, but
        # actual data format varies.
        # Regular: DD-MMM-YYYY Description Amount
        # Installments: DD-MMM-YYYY Description OrigAmount PendingBalance ...
        
        # Simplified regex for regular transactions (Subsection C)
        # e.g., 15-ENE-2023 OXXO ROMA $150.00
        # e.g., 20 FEB 24 SPOTIFY $99.00 (year YY/YYYY/missing)
        regular_pattern = re.compile(
            r"^(\d{1,2}[\s-]\w{3})\s+"  # Date (DD MMM)
            r"(.+?)\s+"                 # Description (non-greedy)
            r"([\$\-\+]?\s*[\d,]+\.\d{2})$",  # Amount
            re.IGNORECASE
        )
        
        # Simplified regex for no-interest installments (Subsection A)
        # e.g., 01-FEB-2023 AMAZON MX $1000.00 $800.00 $200.00 2/5
        no_interest_pattern = re.compile(
            r"^(\d{1,2}[\s-]\w{3})\s+"              # Date (DD MMM)
            r"(.+?)\s+"                             # Description (non-greedy)
            r"([\$\-\+]?\s*[\d,]+\.\d{2})\s+"      # Original Amount
            r"([\$\-\+]?\s*[\d,]+\.\d{2})\s+"      # Pending Balance
            r"([\$\-\+]?\s*[\d,]+\.\d{2})\s+"      # Required Payment
            # Payment No. (e.g., "12 DE 18")
            r"(\d+\s+DE\s+\d+)$"
            ,
            re.IGNORECASE
        )

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = None
            parsed_tx = {}

            if transaction_type == "regular":
                match = regular_pattern.match(line)
                if match:
                    date_str, desc, amount_str = match.groups()
                    parsed_tx = {
                        "operation_date": self._parse_date_with_year_context(
                            date_str, current_year
                        ),
                        "description": desc.strip(),
                        "amount": self._parse_amount(amount_str),
                        "type": "regular"
                    }
            elif transaction_type == "no_interest_installments":
                match = no_interest_pattern.match(line)
                if match:
                    groups = match.groups()
                    date_str, desc, orig_amount_str = groups[0], groups[1], groups[2]
                    pend_bal_str, req_pay_str, pay_num_str = groups[3], groups[4], groups[5]
                    parsed_tx = {
                        "operation_date": self._parse_date_with_year_context(
                            date_str, current_year
                        ),
                        "description": desc.strip(),
                        "original_amount": self._parse_amount(orig_amount_str),
                        "pending_balance": self._parse_amount(pend_bal_str),
                        "required_payment": self._parse_amount(req_pay_str),
                        "payment_number": pay_num_str,
                        "type": "no_interest_installment"
                    }
            # TODO: Add pattern for interest-bearing installments

            # Basic validation: ensure essential fields are present
            if parsed_tx and parsed_tx.get("amount") is not None:
                transactions.append(parsed_tx)
            # If no match but line looks like it might contain data, log it
            elif match is None and len(line.split()) > 2:
                logger.debug(
                    f"Line did not match {transaction_type} pattern. "
                    f"Content: '{line}'"
                )
        
        return transactions

    def _parse_date_with_year_context(self, date_str: str, 
                                      year_context: int) -> Optional[datetime]:
        """Parses date string that might have YY or be missing year, using context."""
        normalized_date_str = self._normalize_date_spanish(date_str.upper())
        
        # Supported formats include:
        # DD-MMM-YYYY, DD-MMM-YY, DD MMM YYYY, DD MMM YY
        # DD/MMM/YYYY, DD/MMM/YY
        # DD-MMM, DD MMM (year inferred from context)
        
        # Check for YYYY (four-digit year) first
        if re.search(r'\d{4}', normalized_date_str):
            return self._parse_date(
                normalized_date_str, ["%d-%b-%Y", "%d %b %Y", "%d/%b/%Y"]
            )
        # Check if date string ends with YY (two-digit year)
        elif re.search(r'\d{2}$', normalized_date_str.split('-')[-1].split(' ')[-1]):
            try:  # Attempt DD-MMM-YY or DD MMM YY formats
                dt = datetime.strptime(normalized_date_str, "%d-%b-%y")
                return dt
            except ValueError:
                try:
                    dt = datetime.strptime(normalized_date_str, "%d %b %y")
                    return dt
                except ValueError:
                    pass  # Continue to other formats if YY parsing fails
        
        # No year or ambiguous year, use context year
        try: # DD-MMM or DD MMM
            dt = datetime.strptime(f"{normalized_date_str} {year_context}", "%d-%b %Y")
            return dt
        except ValueError:
            try:
                dt = datetime.strptime(f"{normalized_date_str} {year_context}", "%d %b %Y")
                return dt
            except ValueError:
                logger.warning(
                    f"Could not parse date '{date_str}' "
                    f"with year context {year_context}"
                )
                return None

    def extract_transaction_details(
        self, full_text: str, pages: List[pdfplumber.page.Page],
        year_context: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extracts all transaction types (Sec. 22) from relevant pages."""
        transactions = {
            "no_interest_installments": [],
            "interest_bearing_installments": [],
            "regular_transactions": [],
        }
        
        # Find start/end of transaction sections using headers.
        # Simplified: robust parsing needs layout analysis or LLM for table boundaries.
        
        # Determine year context from statement period if not provided.
        if year_context is None:
            period_match = re.search(
                self.patterns["statement_period"], full_text, re.IGNORECASE
            )
            if period_match:
                end_date_str = period_match.group(2)
                end_dt = self._parse_date(end_date_str)
                if end_dt:
                    year_context = end_dt.year
            if year_context is None:
                year_context = datetime.now().year  # Fallback
            logger.info(
                f"Using year context for transactions: {year_context}"
            )

        # Iterate through text to find transaction tables
        # This is a very basic way to find tables; pdfplumber's table extraction or LLM would be better.
        current_table_type = None
        table_text_buffer = ""

        lines = full_text.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            
            is_header = False
            no_i_header = self.patterns["no_interest_installments_header"].lower()
            i_header = self.patterns["interest_bearing_installments_header"].lower()
            
            if no_i_header in line_lower:
                if current_table_type and table_text_buffer:
                    tx_list = self._extract_transactions_from_table_text(
                        table_text_buffer, current_table_type, year_context
                    )
                    transactions[current_table_type].extend(tx_list)
                current_table_type = "no_interest_installments"
                table_text_buffer = ""
                is_header = True
            elif i_header in line_lower:
                if current_table_type and table_text_buffer:
                    tx_list = self._extract_transactions_from_table_text(
                        table_text_buffer, current_table_type, year_context
                    )
                    transactions[current_table_type].extend(tx_list)
                current_table_type = "interest_bearing_installments"
                table_text_buffer = ""
                is_header = True
            reg_header = self.patterns["regular_transactions_header"].lower()
            if reg_header in line_lower: # Shortened condition
                if current_table_type and table_text_buffer:
                    tx_list = self._extract_transactions_from_table_text(
                        table_text_buffer, current_table_type, year_context
                    )
                    transactions[current_table_type].extend(tx_list)
                current_table_type = "regular_transactions"
                table_text_buffer = ""
                is_header = True
            
            if current_table_type and not is_header and line.strip():
                # Simple heuristic: if line looks like a date, add to buffer
                # This needs to be much smarter, e.g. checking for amounts, specific keywords
                date_like = re.match(r"^\d{1,2}[\s-]\w{3}", line, re.IGNORECASE)
                amount_like = re.search(r"[\$\-\+]?\s*[\d,]+\.\d{2}", line)
                if date_like or amount_like:
                    table_text_buffer += line + '\n'
        
        # Process the last buffered table
        if current_table_type and table_text_buffer:
            tx_list = self._extract_transactions_from_table_text(
                table_text_buffer, current_table_type, year_context
            )
            transactions[current_table_type].extend(tx_list)

        # Alternative: Use pdfplumber's table extraction (can be more reliable for structured tables)
        # for page_num, page in enumerate(pages):
        #     tables = page.extract_tables()
        #     for table_idx, table_data in enumerate(tables):
        #         # Here, you'd need to identify which type of transaction table it is
        #         # based on headers or surrounding text, then parse table_data.
        #         logger.debug(f"Page {page_num+1}, Table {table_idx+1} found with {len(table_data)} rows.")
        #         # Example: Pass table_data (list of lists) to a specialized table parser

        logger.info(
            f"Extracted transactions: "
            f"No-Interest: {len(transactions['no_interest_installments'])}, "
            f"Interest-Bearing: {len(transactions['interest_bearing_installments'])}, "
            f"Regular: {len(transactions['regular_transactions'])}"
        )
        return transactions

    def extract_summary_and_payment_info(
        self, page_text: str
    ) -> Dict[str, Any]:
        """Extracts summary & payment info (Sec 5-7) using LLM."""
        summary_data = {}
        if not self.llm_service:
            logger.warning(
                "LLM service not available for summary/payment info extraction."
            )
            return summary_data

        prompt = (
            f"Extract the following financial details from the provided bank "
            f"statement text. Focus on sections typically titled 'Resumen de Cargos', "
            f"'Resumen del Periodo', 'Cómo Pagar', or similar "
            f"summary sections. "
            f"Return the information as a JSON object with the following keys "
            f"(use null if not found):\n"
            f"- previous_balance (Saldo Anterior / "
            f"Adeudo del periodo anterior)\n"
            f"- payments_and_credits (Pagos y Abonos)\n"
            f"- regular_charges (Cargos Regulares / Compras y Cargos)\n"
            f"- installment_charges (Cargos por "
            f"Compras a Meses)\n"
            f"- interest_charged (Intereses del Periodo / Intereses Cobrados)\n"
            f"- commissions (Comisiones)\n"
            f"- vat_iva (IVA / Impuestos)\n"
            f"- new_balance (Nuevo Saldo / Saldo Actual / Total a Pagar)\n"
            f"- minimum_payment (Pago Mínimo)\n"
            f"- pay_to_avoid_interest (Pago para no Generar Intereses)\n"
            f"- payment_due_date (Fecha Límite de Pago)\n"
            f"- credit_limit (Límite de Crédito)\n"
            f"- available_credit (Crédito Disponible)\n\n"
            f"Text to analyze:\n"
            f"---BEGIN TEXT---\n"
            f"{page_text}\n"
            f"---END TEXT---\n\n"
            f"Respond ONLY with the JSON object."
        )

        try:
            raw_response = self.llm_service.generate(prompt)
            # Assuming the LLM returns a JSON string, possibly with markdown
            json_markdown_pattern = r"```json\n(.*\n)```"
            json_response_match = re.search(json_markdown_pattern, raw_response, re.DOTALL)
            if json_response_match:
                json_str = json_response_match.group(1).strip()
            else:
                # Fallback if no markdown code block, assume raw JSON string
                json_str = raw_response.strip()
            
            llm_extracted_data = json.loads(json_str)

            amount_keys = [
                "previous_balance", "payments_and_credits", "regular_charges",
                "installment_charges", "interest_charged", "commissions",
                "vat_iva", "new_balance", "minimum_payment", 
                "pay_to_avoid_interest", "credit_limit", "available_credit"
            ]

            for key, value in llm_extracted_data.items():
                if value is not None:
                    if key in amount_keys:
                        summary_data[key] = self._parse_amount(str(value))
                    elif key == "payment_due_date": 
                        # Assuming LLM provides date in a parsable format.
                        # For now, store as string. Future: self._parse_date(str(value))
                        summary_data[key] = str(value)
                    else:
                        summary_data[key] = str(value)

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode LLM JSON response for summary: {e}"
            )
            logger.debug(f"LLM raw response for summary: {raw_response}")
        except Exception as e:
            logger.error(f"Error during LLM summary extraction: {e}")
            raw_resp_debug = raw_response if 'raw_response' in locals() else 'N/A'
            logger.debug(
                f"LLM raw response for summary (if available): {raw_resp_debug}"
            )

        # Commenting out old regex logic
        # patterns_sec7 = {
        #     "previous_balance": r"Adeudo del periodo anterior\s*\$([\d,]+\.\d{2})",
        #     "regular_charges": r"Cargos regulares \(no a meses\)\s*\$([\d,]+\.\d{2})",
        #     "payments_and_credits": r"Pagos y abonos\s*\$([\d,]+\.\d{2})", # Often negative
        # }
        # for key, pattern in patterns_sec7.items():
        #     match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
        #     if match:
        #         summary_data[key] = self._parse_amount(match.group(1))

        logger.info(
            f"Extracted summary/payment info (LLM): {summary_data}"
        )
        return summary_data

    def create_llm_prompts_for_sections(self, section_texts: Dict[str, str]) -> Dict[str, str]:
        """Creates LLM prompt templates for structured section identification.
           Placeholder: Returns example prompts.
        """
        prompts = {}
        for section_name, text_content in section_texts.items():
            prompts[section_name] = (
                f"Extract the key information from the following text of section '{section_name}' "
                f"from a Mexican credit card statement according to CONDUSEF regulations. "
                f"Format the output as a JSON object. Text:\n\n{text_content}"
            )
        return prompts

    def create_llm_prompts_for_transactions(self, table_texts: Dict[str, str]) -> Dict[str, str]:
        """Designs specialized transaction extraction prompts for each table type.
           Placeholder: Returns example prompts.
        """
        prompts = {}
        transaction_type_map = {
            "no_interest_installments": "COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES",
            "interest_bearing_installments": "COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES",
            "regular_transactions": "CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)"
        }
        for tx_type_key, table_text in table_texts.items():
            full_tx_type_name = transaction_type_map.get(tx_type_key, tx_type_key)
            prompts[tx_type_key] = (
                f"Extract all transactions from the following table text which corresponds to '{full_tx_type_name}'. "
                f"Each transaction should be a JSON object with fields like 'operation_date', 'description', 'amount'. "
                f"For installment transactions, include 'original_amount', 'pending_balance', 'required_payment', 'payment_number'. "
                f"Ensure dates are in YYYY-MM-DD format. Text:\n\n{table_text}"
            )
        return prompts

    def parse(self, full_text: str, pdf_pages: List[pdfplumber.page.Page], file_path: Optional[str] = None) -> Dict[str, Any]:
        """Main parsing method, using pre-extracted text and PDF page objects."""
        extracted_data = {
            "document_type": "unknown",
            "primary_info": {},
            "transactions": {},
            "summary_info": {},
            "errors": [],
            "raw_text_by_page": []
        }
        try:
            # Use pre-extracted text and pages
            all_pages_content = [page.extract_text() or "" for page in pdf_pages]
            # Populate raw_text_by_page for consistency with previous structure if needed by caller
            extracted_data["raw_text_by_page"] = all_pages_content

            if not full_text.strip():
                log_msg = "No text content provided for parsing."
                if file_path: 
                    log_msg += f" (File: {file_path})"
                extracted_data["errors"].append(log_msg)
                logger.warning(log_msg)
                return extracted_data

            extracted_data["document_type"] = self.classify_document_type(full_text)
            
            if extracted_data["document_type"] == "credit_card_statement_condusef":
                # Page 1 for primary info
                if len(all_pages_content) > 0:
                    extracted_data["primary_info"] = self.extract_primary_information(all_pages_content[0])
                    # Summary info also often on page 1 or early pages
                    extracted_data["summary_info"] = self.extract_summary_and_payment_info(all_pages_content[0])
                else:
                    log_msg = "PDF has no pages to extract primary info from."
                    if file_path: 
                        log_msg += f" (File: {file_path})"
                    extracted_data["errors"].append(log_msg)
                    logger.warning(log_msg)

                # Transaction details (Page 2+)
                # Determine year context from primary info if possible
                year_context = None
                if extracted_data["primary_info"].get("statement_period_end") and isinstance(extracted_data["primary_info"]["statement_period_end"], datetime):
                    year_context = extracted_data["primary_info"]["statement_period_end"].year
                
                # Pass pdf_pages (List[pdfplumber.page.Page]) to transaction extractor
                extracted_data["transactions"] = self.extract_transaction_details(full_text, pdf_pages, year_context)
            else:
                log_msg = (f"Document classified as '{extracted_data['document_type']}', "
                           f"skipping CONDUSEF-specific parsing.")
                if file_path: 
                    log_msg += f" (File: {file_path})"
                logger.info(log_msg)
                extracted_data["errors"].append(f"Document not classified as CONDUSEF credit card statement (type: {extracted_data['document_type']}).")

        except Exception as e:
            log_msg = "Error during CONDUSEF parsing"
            if file_path: 
                log_msg += f" for PDF {file_path}"
            log_msg += f": {str(e)}"
            logger.error(log_msg, exc_info=True)
            extracted_data["errors"].append(f"Critical CONDUSEF parsing error: {str(e)}")
        
        return extracted_data

# Example Usage (for testing)
if __name__ == '__main__':
    # This requires a sample PDF. For now, we'll test individual methods with mock data.
    parser = CondusefParser()
    
    # Test date parsing
    print("--- Date Parsing Tests ---")
    print(f"'15-ENE-2023': {parser._parse_date('15-ENE-2023')}")
    print(f"'28 FEB 2024': {parser._parse_date('28 FEB 2024')}")
    print(f"'05/MAR/23': {parser._parse_date_with_year_context('05 MAR 23', 2023)}") # Needs _parse_date_with_year_context
    print(f"'10 ABR': {parser._parse_date_with_year_context('10 ABR', 2023)}")

    # Test amount parsing
    print("\n--- Amount Parsing Tests ---")
    print(f"'$1,234.56': {parser._parse_amount('$1,234.56')}")
    print(f"'500.00': {parser._parse_amount('500.00')}")

    # Test document classification (mock text)
    print("\n--- Document Classification Tests ---")
    mock_statement_text = """
    Estado de Cuenta\nFecha de corte: 15-ENE-2023\nPago mínimo: $500.00\n
    COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES\n    10-ENE-2023 TIENDA XYZ $100.00
    """
    mock_other_text = "Factura de servicio telefónico"
    print(f"Statement text classification: {parser.classify_document_type(mock_statement_text)}")
    print(f"Other text classification: {parser.classify_document_type(mock_other_text)}")

    # Test primary information extraction (mock text)
    print("\n--- Primary Information Extraction Tests ---")
    mock_page1_text = """
    Página 1 de 5
    JUAN PEREZ GARCIA
    CALLE FALSA 123, COLONIA CENTRO, CP 06000, CIUDAD DE MEXICO
    RFC: PEGJ800101H00
    Tarjeta Clásica Internacional
    Número de Tarjeta: 1234 5678 1234 5678
    Periodo: 01-ENE-2023 al 31-ENE-2023
    Fecha de corte: 31-ENE-2023
    Fecha límite de pago: 20-FEB-2023
    Pago para no generar intereses: $5,000.00
    Pago mínimo: $250.00
    """
    primary_info = parser.extract_primary_information(mock_page1_text)
    print(f"Primary Info: {primary_info}")

    # Test transaction extraction (mock text)
    print("\n--- Transaction Extraction Tests ---")
    mock_transactions_text_regular = """
    CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
    02-ENE-2023 OXXO $55.80
    03 ENE 2023 STARBUCKS $120.00
    05-ENE-23 RESTAURANTE LA FLOR $450.30
    10 ENE PAGO RECIBIDO GRACIAS -$2000.00 
    """
    mock_transactions_text_msi = """
    COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES
    01-ENE-2023 AMAZON COMPRA MSI $1200.00 $1000.00 $200.00 1/6
    15-JAN-2023 LIVERPOOL MSI $3000.00 $2500.00 $500.00 2/6
    """
    
    # For transaction extraction, we'd typically use the full_text and page objects
    # Here we simulate calling _extract_transactions_from_table_text directly
    regular_tx = parser._extract_transactions_from_table_text(mock_transactions_text_regular, "regular_transactions", 2023)
    print(f"Regular Transactions: {regular_tx}")
    msi_tx = parser._extract_transactions_from_table_text(mock_transactions_text_msi, "no_interest_installments", 2023)
    print(f"No-Interest Installments: {msi_tx}")

    # To test the full parse method, you would need a PDF file and extract its text/pages first:
    # with pdfplumber.open('path/to/your/sample_statement.pdf') as pdf:
    #     full_text_content = "".join([p.extract_text() or "" for p in pdf.pages])
    #     results = parser.parse(full_text_content, pdf.pages, 'path/to/your/sample_statement.pdf')
    #     print(f"\n--- Full Parse Results ---")
    #     import json
    #     print(json.dumps(results, indent=2, default=str)) # Use default=str for datetime objects
