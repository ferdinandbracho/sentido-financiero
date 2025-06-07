import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import pdfplumber
import dateutil.parser

logger = logging.getLogger(__name__)

class PDFStatementParser:
    """
    Advanced PDF parser for Mexican bank statements
    Supports multiple banks: BBVA, Banamex, Santander, etc.
    """
    
    def __init__(self):
        # Define bank-specific transaction patterns
        self.bank_transaction_patterns = {
            'bbva': [
                # Pattern for BBVA with operation date, charge date, description and amount with +/- sign
                r'(\d{2}-\w{3}-\d{4})\s+(\d{2}-\w{3}-\d{4})\s+(.+?)\s+([\+\-]?\s*\$[\d,]+\.\d{2})',
                # Alternative pattern with day-month-year format
                r'(\d{1,2}[/-]\w{3}[/-]\d{2,4})\s+(\d{1,2}[/-]\w{3}[/-]\d{2,4})\s+(.+?)\s+([\+\-]?\s*\$[\d,]+\.\d{2})',
                # Pattern with just one date and description
                r'(\d{1,2}[/-]\w{3}[/-]\d{2,4})\s+(.+?)\s+([\+\-]?\s*\$[\d,]+\.\d{2})',
                # Pattern with numeric dates (dd/mm/yyyy)
                r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+([\+\-]?\s*\$[\d,]+\.\d{2})',
                # BBVA specific pattern for credit card statements with date prefix in description
                # Format: -YYYY DESCRIPTION + $AMOUNT (credits)
                r'-(?P<year>\d{4})\s+(?P<description>.+?)\s+\+\s+\$(?P<amount>\d[\d,]*\.\d{2})',
                # BBVA payment pattern (debits)
                r'-(?P<year>\d{4})\s+(?P<description>BMOVIL\.PAGO TDC.+?)\s+-\s+\$(?P<amount>\d[\d,]*\.\d{2})',
                # Generic BBVA transaction with date prefix (captures all other transactions)
                r'-(?P<year>\d{4})\s+(?P<description>.+?)(?:\s+(?P<sign>[\+\-])\s+)?\$(?P<amount>\d[\d,]*\.\d{2})',
                # Pattern with just description and amount (for when dates are on separate lines)
                r'([A-Z0-9\s.,\-\*]+)\s+([\+\-]?\s*\$[\d,]+\.\d{2})'
            ],
            'banamex': [
                r'(\d{2}/\d{2})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})',
                r'(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})'
            ],
            'santander': [
                r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})'
            ],
            'hsbc': [
                r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})'
            ],
            'scotiabank': [
                r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})'
            ]
        }
        
        # Define generic transaction patterns for fallback
        self.generic_transaction_patterns = [
            # Generic date + description + amount pattern
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})',
            # Generic pattern with Spanish month abbreviations
            r'(\d{1,2}[/-]\w{3}[/-]\d{2,4})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})',
            # Pattern with just description and amount
            r'([A-Z0-9\s.,\-\*]+)\s+([\+\-]?\$[\d,]+\.\d{2})'
        ]
        
        self.bank_patterns = {
            'bbva': {
                'name': 'BBVA',
                'account_pattern': r'Número de tarjeta:\s*(\d{16})',
                'period_pattern': (
                    r'Periodo:\s*(\d{2}-\w{3}-\d{4})\s*al\s*(\d{2}-\w{3}-\d{4})'
                ),
                'holder_pattern': r'^([A-Z\s]+)\s*$',
                'transaction_pattern': (
                    r'(\d{2}-\w{3}-\d{4})\s+(\d{2}-\w{3}-\d{4})\s+(.+?)\s+'
                    r'([\+\-]?\s*\$[\d,]+\.\d{2})'
                ),
            },
            'banamex': {
                'name': 'Banamex',
                'account_pattern': (
                    r'Número de cuenta:\s*(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})'
                ),
                'period_pattern': (
                    r'Periodo del\s*(\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4})'
                    r'\s+al\s+(\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4})'
                ),
                'holder_pattern': r'Titular:\s*(.+)',
                'transaction_pattern': r'(\d{2}/\d{2})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})',
            },
            'santander': {
                'name': 'Santander',
                'account_pattern': r'Cuenta:\s*(\d+)',
                'period_pattern': r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})',
                'holder_pattern': r'([A-Z\s]+)',
                'transaction_pattern': r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})',
            },
            'hsbc': {
                'name': 'HSBC',
                'account_pattern': r'Cuenta\s*[Nn]o\.?\s*(\d+)',
                'period_pattern': (
                    r'(?:Periodo|Estado de Cuenta)[^\n]*?\s*(\d{2}[/-]\d{2}[/-]\d{4})'
                    r'\s*(?:al|a|hasta|-)\s*(\d{2}[/-]\d{2}[/-]\d{4})'
                ),
                'holder_pattern': r'(?:Nombre|Cliente):\s*([A-Z\s]+)',
                'transaction_pattern': r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})',
            },
            'scotiabank': {
                'name': 'Scotiabank',
                'account_pattern': r'(?:Cuenta|Tarjeta)\s*[Nn]o\.?\s*(\d+)',
                'period_pattern': (
                    r'(?:Periodo|Del)\s+(\d{2}[/-]\w{3}[/-]\d{4})'
                    r'\s*(?:al|a|hasta|-)\s*(\d{2}[/-]\w{3}[/-]\d{4})'
                ),
                'holder_pattern': r'(?:Nombre|Cliente):\s*([A-Z\s]+)',
                'transaction_pattern': r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\+\-]?\$[\d,]+\.\d{2})',
            }
        }
        
        # Mexican month translations
        self.month_translations = {
            'ene': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'abr': 'Apr',
            'may': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug',
            'sep': 'Sep', 'oct': 'Oct', 'nov': 'Nov', 'dic': 'Dec',
            'enero': 'Jan', 'febrero': 'Feb', 'marzo': 'Mar', 'abril': 'Apr',
            'mayo': 'May', 'junio': 'Jun', 'julio': 'Jul', 'agosto': 'Aug',
            'septiembre': 'Sep', 'octubre': 'Oct', 'noviembre': 'Nov', 'diciembre': 'Dec'
        }

    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Main entry point for PDF parsing
        Returns structured data from bank statement
        
        This method uses a tiered approach to parsing:
        1. First, try universal standardized parsing for Mexican credit card statements
        2. If that fails or has low confidence, try bank-specific parsing if bank is detected
        3. Fall back to generic parsing as a last resort
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract text from all pages with enhanced robustness
                full_text = self._extract_text_from_pdf(pdf)
                
                # If we couldn't extract enough text, log a warning
                if len(full_text.strip()) < 100:
                    logging.warning("Extracted very little text from PDF, parsing may be incomplete")
                
                # Detect bank type using universal approach
                bank_type = self._detect_bank_type(full_text, file_path)
                logging.info(f"Detected bank type: {bank_type}")
                
                # First try universal parsing approach (optimized for Mexican statements)
                logging.info("Using universal standardized parsing approach")
                try:
                    result = self._parse_universal_statement(full_text, pdf, bank_type, file_path)
                    logging.info("Universal parsing completed successfully")
                except Exception as e:
                    logging.error(f"Error in _parse_universal_statement: {str(e)}")
                    # Create a minimal result to avoid further errors
                    result = {
                        'bank_name': bank_type.capitalize() if bank_type else "Unknown",
                        'account_holder': "Unknown",
                        'account_number': "Unknown",
                        'statement_period_start': None,
                        'statement_period_end': None,
                        'transactions': [],
                        'summary': {},
                        'parsing_confidence': 0.0,
                        'parsing_method': 'error_recovery'
                    }
                    
                # Check if universal parsing was successful
                if result.get('parsing_confidence', 0) < 0.5 or not result.get('transactions'):
                    # If universal parsing failed or had low confidence, try bank-specific parsing
                    if bank_type and bank_type in self.bank_patterns:
                        logging.info(f"Universal parsing had low confidence. Trying {bank_type}-specific parsing")
                        bank_result = self._parse_bank_statement(full_text, bank_type, pdf)
                        
                        # Use bank-specific result if it has higher confidence
                        if bank_result.get('parsing_confidence', 0) > result.get('parsing_confidence', 0):
                            result = bank_result
                            logging.info(f"Using {bank_type}-specific parsing results")
                    else:
                        # Fall back to generic parsing if universal parsing failed and no bank-specific parsing available
                        logging.info("Universal parsing failed. Using generic parsing as fallback")
                        generic_result = self._parse_generic_statement(full_text, pdf)
                        
                        # Use generic result if it has higher confidence
                        if generic_result.get('parsing_confidence', 0) > result.get('parsing_confidence', 0):
                            result = generic_result
                            logging.info("Using generic parsing results")
                
                return result
                
        except Exception as e:
            logging.error(f"Error parsing PDF: {str(e)}")
            raise

    def _extract_text_from_pdf(self, pdf) -> str:
        """Extract and clean text from all PDF pages with enhanced robustness"""
        full_text = ""
        try:
            # Try standard extraction first
            for page in pdf.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                        logger.debug(f"Extracted {len(page_text)} characters from page")
                    else:
                        logger.warning(f"No text extracted from page {pdf.pages.index(page) + 1}")
                except Exception as e:
                    logger.warning(f"Error extracting text from page: {str(e)}")
            
            # If we got very little text, try alternative extraction methods
            if len(full_text.strip()) < 100:
                logger.warning("Standard PDF extraction yielded minimal results, trying alternative method")
                # Try extracting tables as a fallback
                for page in pdf.pages:
                    try:
                        tables = page.extract_tables()
                        for table in tables:
                            for row in table:
                                full_text += " ".join([cell or "" for cell in row]) + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting tables: {str(e)}")
            
            return full_text
        except Exception as e:
            logger.error(f"Error in PDF text extraction: {str(e)}")
            return full_text

    def _detect_bank_type(self, text: str, filename: str = "") -> str:
        """Detect bank type from PDF content using a universal approach"""
        text_lower = text.lower()
        
        # Common bank identifiers for Mexican banks
        bank_indicators = {
            'bbva': ['bbva', 'bancomer', 'tarjeta platinum bbva', 'bbva méxico', 'bbva bancomer'],
            'banamex': ['banamex', 'citibanamex', 'banco nacional de méxico'],
            'santander': ['santander', 'banco santander', 'santander like', 'santander méxico', 
                         'tarjeta de crédito santander'],
            'hsbc': ['hsbc', 'hsbc méxico', 'hsbc bank'],
            'scotiabank': ['scotiabank', 'scotia', 'scotiabank inverlat'],
            'banorte': ['banorte', 'banco mercantil del norte']
        }
        
        # Step 1: Try with exact bank name detection in text
        for bank, indicators in bank_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                logger.info(f"Detected bank: {bank} using exact match in text")
                return bank
        
        # Step 2: Look for bank RFC (tax ID) patterns
        rfc_patterns = {
            'bbva': r'BBA830831LJ2',
            'santander': r'BSM970519DU8',
            'banamex': r'BNM840515VB1',
            'hsbc': r'HMI950125KI8',
            'scotiabank': r'SIN941202514',
            'banorte': r'BMN930209927'
        }
        
        for bank, pattern in rfc_patterns.items():
            if re.search(pattern, text):
                logger.info(f"Detected bank: {bank} using RFC pattern")
                return bank
        
        # Step 3: Try with more aggressive pattern matching in text
        for bank, indicators in bank_indicators.items():
            for indicator in indicators:
                # Check for partial matches or variations
                if any(word in indicator or indicator in word for word in text_lower.split()):
                    logger.info(f"Detected bank: {bank} using partial match in text")
                    return bank
        
        # Step 4: Try to detect from filename if provided
        if filename:
            filename_lower = filename.lower()
            for bank, indicators in bank_indicators.items():
                if any(indicator in filename_lower for indicator in indicators):
                    logger.info(f"Detected bank: {bank} from filename")
                    return bank
        
        # Step 5: Look for standardized section headers that might indicate bank type
        section_patterns = {
            'bbva': [r'estado de cuenta bbva', r'resumen integral bbva'],
            'santander': [r'estado de cuenta santander', r'resumen de movimientos santander'],
            'banamex': [r'estado de cuenta banamex', r'resumen de cuenta banamex'],
            'hsbc': [r'estado de cuenta hsbc', r'resumen de cuenta hsbc'],
            'scotiabank': [r'estado de cuenta scotia', r'resumen de cuenta scotiabank'],
            'banorte': [r'estado de cuenta banorte', r'resumen de cuenta banorte']
        }
        
        for bank, patterns in section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    logger.info(f"Detected bank: {bank} using section pattern")
                    return bank
        
        logger.warning("Could not detect bank type from statement")
        return None

    def _parse_bank_statement(self, text: str, bank_type: str, pdf) -> Dict[str, Any]:
        """Parse statement using bank-specific patterns"""
        patterns = self.bank_patterns[bank_type]
        
        result = {
            'bank_name': patterns['name'],
            'raw_text': text,
            'parsing_method': f'{bank_type}_specific',
            'account_holder': self._extract_account_holder(text, patterns),
            'account_number': self._extract_account_number(text, patterns),
            'statement_period': self._extract_statement_period(text, patterns),
            'transactions': self._extract_transactions(text, patterns, bank_type),
            'summary': self._extract_summary_info(text, bank_type),
            'parsing_confidence': 0.9
        }
        
        return result
        
    def _parse_universal_statement(self, text: str, pdf=None, bank_type: str = None, filename: str = "") -> Dict[str, Any]:
        """Parse statement using universal approach for standardized Mexican credit card statements
        
        This method implements a universal parsing approach based on the standardized
        format required for all Mexican credit card statements. It extracts metadata
        and transactions using standardized extraction methods and falls back to
        bank-specific patterns only when needed.
        """
        logging.info("Parsing statement using universal approach")
        
        # Initialize variables with safe defaults
        bank_name = "Unknown"
        account_holder = "Unknown"
        account_number = "Unknown"
        start_date = None
        end_date = None
        transactions = []
        summary = {}
        confidence = 0.0
        
        try:
            # Determine bank name
            if bank_type:
                bank_name = self.bank_patterns.get(bank_type.lower(), {}).get('name', bank_type.capitalize())
                logging.debug(f"Bank name: {bank_name}")
                
            # Extract account holder using standardized method
            try:
                account_holder = self._extract_standardized_account_holder(text)
                logging.debug(f"Account holder: {account_holder}")
            except Exception as e:
                logging.error(f"Error extracting account holder: {str(e)}")
                account_holder = "Unknown"
            
            # Extract account number using standardized patterns
            try:
                account_number = self._extract_standardized_account_number(text)
                logging.debug(f"Account number: {account_number}")
            except Exception as e:
                logging.error(f"Error extracting account number: {str(e)}")
                account_number = "Unknown"
            
            # Extract statement period using standardized patterns
            try:
                logging.debug("Attempting to extract statement period")
                period_result = self._extract_standardized_statement_period(text)
                logging.debug(f"Period result type: {type(period_result)}, value: {period_result}")
                
                if period_result and isinstance(period_result, tuple) and len(period_result) == 2:
                    start_date, end_date = period_result
                    logging.debug(f"Extracted period: {start_date} to {end_date}")
                else:
                    logging.debug("Using statement period extraction fallback")
                    # Fallback to enhanced period extraction with bank_type
                    start_date, end_date = self._extract_statement_period_fallback(text, bank_type)
                    logging.debug(f"Fallback period result: {start_date} to {end_date}")
                    
                    # Store the statement period for use in transaction date extraction
                    self.statement_period = (start_date, end_date)
            except Exception as e:
                logging.error(f"Error extracting statement period: {str(e)}")
                start_date, end_date = None, None
            
            # Extract transactions using standardized format - pass bank_type to help with bank-specific patterns
            try:
                logging.debug("Attempting to extract transactions")
                transactions = self._extract_standardized_transactions(text, bank_type)
                logging.debug(f"Transaction extraction result type: {type(transactions)}")
                if transactions is None:
                    logging.warning("Transaction extraction returned None, using empty list instead")
                    transactions = []
                logging.debug(f"Found {len(transactions)} transactions")
            except Exception as e:
                logging.error(f"Error extracting transactions: {str(e)}")
                transactions = []
            
            # Extract summary information
            try:
                # Try to extract summary or use empty dict as fallback
                try:
                    summary = self._extract_standardized_summary(text)
                except AttributeError:
                    # Use bank-specific summary extraction if available
                    if bank_type and bank_type.lower() in self.bank_patterns:
                        summary = self._extract_summary_info(text, bank_type)
                    else:
                        summary = {}
                    logging.warning("Using fallback summary extraction method")
                logging.debug(f"Summary: {summary}")
            except Exception as e:
                logging.error(f"Error extracting summary: {str(e)}")
                summary = {}
            confidence = 0.0
            if account_holder and account_holder != "Unknown":
                confidence += 0.2
            if account_number and account_number != "Unknown":
                confidence += 0.2
            if start_date and end_date:
                confidence += 0.2
            if transactions:
                confidence += 0.2 + min(0.2, len(transactions) / 50 * 0.2)  # More transactions = higher confidence
            
            logging.debug(f"Parsing confidence: {confidence}")
            
        except Exception as e:
            logging.error(f"Unexpected error in universal parsing: {str(e)}")
            # Continue with default values already set
        
        # Create result dictionary with all extracted data
        result = {
            'bank_name': bank_name,
            'account_holder': account_holder,
            'account_number': account_number,
            'statement_period_start': start_date,
            'statement_period_end': end_date,
            'transactions': transactions,
            'summary': summary,
            'parsing_confidence': confidence,
            'parsing_method': 'universal_standardized'
        }
        
        # If we have bank-specific patterns, enhance with bank-specific data
        try:
            if bank_type and bank_type.lower() in self.bank_patterns:
                bank_patterns = self.bank_patterns[bank_type.lower()]
                
                # Only use bank-specific patterns if universal extraction failed
                if not account_holder or account_holder == "Unknown":
                    result['account_holder'] = self._extract_account_holder(text, bank_patterns)
                
                if not account_number or account_number == "Unknown":
                    result['account_number'] = self._extract_account_number(text, bank_patterns)
                
                if not (start_date and end_date):
                    start, end = self._extract_statement_period(text, bank_patterns)
                    if start and end:
                        result['statement_period_start'] = start
                        result['statement_period_end'] = end
                
                # Only use bank-specific transaction extraction if universal extraction failed
                if not transactions and 'transaction_pattern' in bank_patterns:
                    try:
                        bank_transactions = self._extract_transactions(text, bank_patterns, bank_type)
                        if bank_transactions and isinstance(bank_transactions, list):
                            result['transactions'] = bank_transactions
                    except Exception as e:
                        logging.error(f"Error in bank-specific transaction extraction: {str(e)}")
        except Exception as e:
            logging.error(f"Error in bank-specific enhancement: {str(e)}")
        
        # Fall back to generic extraction methods if needed
        try:
            # No need to implement generic extraction methods - use bank-specific ones as fallbacks
            if not result['account_holder'] or result['account_holder'] == "Unknown":
                # Use BBVA method as fallback for any bank
                try:
                    bbva_patterns = self.bank_patterns.get('bbva', {})
                    result['account_holder'] = self._extract_account_holder(text, bbva_patterns)
                    logging.warning("Using BBVA account holder extraction as generic fallback")
                except Exception as e:
                    logging.error(f"Error in fallback account holder extraction: {str(e)}")
            
            if not result['account_number'] or result['account_number'] == "Unknown":
                # Use BBVA method as fallback for any bank
                try:
                    bbva_patterns = self.bank_patterns.get('bbva', {})
                    result['account_number'] = self._extract_account_number(text, bbva_patterns)
                    logging.warning("Using BBVA account number extraction as generic fallback")
                except Exception as e:
                    logging.error(f"Error in fallback account number extraction: {str(e)}")
        except Exception as e:
            logging.error(f"Error in generic fallback extraction: {str(e)}")
            
        return result
        
    def _parse_generic_statement(self, text: str, pdf) -> Dict[str, Any]:
        """Parse statement using generic patterns (fallback method)"""
        result = {
            'bank_name': "Unknown",
            'raw_text': text,
            'parsing_method': 'generic',
            'account_holder': self._extract_generic_account_holder(text),
            'account_number': self._extract_generic_account_number(text),
            'statement_period': self._extract_generic_statement_period(text),
            'transactions': self._extract_generic_transactions(text),
            'summary': {},
            'parsing_confidence': 0.5
        }
        
        return result

    def _extract_account_holder(self, text: str, patterns: Dict) -> Optional[str]:
        """Extract account holder name"""
        # First try pattern-based extraction
        pattern = patterns.get('holder_pattern')
        if pattern:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # For BBVA, try specific extraction
        if 'bbva' in patterns.get('name', '').lower():
            # Look for name in specific format used in BBVA statements
            bbva_name_pattern = r'([A-Z][A-Z\s]+(?:BRACHO|CARDOZA|RODRIGUEZ|MARTINEZ|GONZALEZ|HERNANDEZ|LOPEZ|GARCIA|PEREZ|SANCHEZ|RAMIREZ|TORRES|FLORES|VAZQUEZ|DIAZ))'
            match = re.search(bbva_name_pattern, text)
            if match:
                return match.group(1).strip()
                
            # Try line-by-line for all-caps names in first 15 lines
            lines = text.split('\n')
            for line in lines[:15]:
                line = line.strip()
                if len(line) > 10 and line.isupper() and not any(char.isdigit() for char in line):
                    # Remove common bank terms
                    line = re.sub(r'\b(BBVA|BANCOMER|ESTADO|CUENTA|TARJETA|CREDITO)\b', '', line).strip()
                    if len(line) > 5:
                        return line
        
        return None

    def _extract_account_number(self, text: str, patterns: Dict) -> Optional[str]:
        """Extract account or card number"""
        pattern = patterns.get('account_pattern')
        if pattern:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # Generic patterns for card/account numbers
        generic_patterns = [
            r'Número de tarjeta:\s*(\d{16})',
            r'Cuenta:\s*(\d+)',
            r'Tarjeta:\s*(\d+)',
            r'No\.\s*(\d{10,})'
        ]
        
        for pattern in generic_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def _extract_statement_period(self, text: str, patterns: Dict) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Extract statement period dates"""
        pattern = patterns.get('period_pattern')
        if pattern:
            match = re.search(pattern, text)
            if match:
                try:
                    start_date = self._parse_date(match.group(1))
                    end_date = self._parse_date(match.group(2))
                    return start_date, end_date
                except:
                    pass
        
        return None, None

    def _extract_transactions(self, text: str, patterns: Dict[str, Any], bank_type: str) -> List[Dict[str, Any]]:
        """Extract transactions from statement text using a universal approach"""
        transactions = []
        
        try:
            # First try using standardized Mexican credit card statement format
            standardized_transactions = self._extract_standardized_transactions(text, bank_type)
            if standardized_transactions and isinstance(standardized_transactions, list):
                logger.info(f"Extracted {len(standardized_transactions)} transactions using standardized format")
                return standardized_transactions
            
            # If standardized extraction fails, fall back to bank-specific patterns
            transaction_patterns = patterns.get('transaction_patterns', [])
            if not transaction_patterns:
                logger.warning(f"No transaction patterns defined for {bank_type}")
                return []
            
            # Process each line for transactions
            lines = text.split('\n')
            for line in lines:
                if self._is_transaction_line(line, bank_type):
                    for pattern in transaction_patterns:
                        transaction = self._parse_transaction_line(line, pattern, bank_type)
                        if transaction:
                            transactions.append(transaction)
                            break
        except Exception as e:
            logger.error(f"Error in _extract_transactions: {str(e)}")
            return []
        
        return transactions
    
    # Implementation of missing standardized methods that use BBVA methods as fallbacks
    def _extract_standardized_account_holder(self, text: str) -> str:
        """Extract account holder using standardized patterns for Mexican statements"""
        # Use BBVA patterns as a fallback
        bbva_patterns = self.bank_patterns.get('bbva', {})
        return self._extract_account_holder(text, bbva_patterns)
    
    def _extract_standardized_account_number(self, text: str) -> str:
        """Extract account number using standardized patterns for Mexican statements"""
        # Use BBVA patterns as a fallback
        bbva_patterns = self.bank_patterns.get('bbva', {})
        return self._extract_account_number(text, bbva_patterns)
    
    def _extract_standardized_statement_period(self, text: str) -> Tuple[datetime, datetime]:
        """Extract statement period using standardized patterns for Mexican statements"""
        # Use BBVA patterns as a fallback
        bbva_patterns = self.bank_patterns.get('bbva', {})
        return self._extract_statement_period(text, bbva_patterns)
    
    def _extract_standardized_summary(self, text: str) -> Dict[str, Any]:
        """Extract summary information using standardized patterns for Mexican statements"""
        # Use bank-specific summary extraction as a fallback
        return self._extract_summary_info(text)
    
    def _extract_standardized_transactions(self, text: str, bank_type: str = None) -> List[Dict[str, Any]]:
        """Extract transactions using standardized patterns"""
        if not text:
            logging.warning("No text provided for transaction extraction")
            return []
            
        # For debugging, log the first 1000 characters of the text
        logging.debug(f"First 1000 chars of text: {text[:1000]}...")
            
        transactions = []
        
        try:
            text_lines = text.split('\n')
            
            # Transaction section headers
            transaction_section_headers = [
                r'(?:DESGLOSE DE MOVIMIENTOS)',  # BBVA
                r'(?:CARGOS, COMPRAS Y ABONOS REGULARES\(NO A MESES\))',  # BBVA
                r'(?:MOVIMIENTOS DEL PERIODO)',  # Santander
                r'(?:DETALLE DE MOVIMIENTOS)',  # Banamex
                r'(?:RELACIÓN DE MOVIMIENTOS)',  # Generic
                r'(?:TRANSACCIONES)',  # Generic
                r'(?:DETALLE DE OPERACIONES)',  # Generic
                r'(?:COMPRAS Y DISPOSICIONES)',  # BBVA
                r'(?:CARGOS Y ABONOS)',  # BBVA
            ]
            
            # Log all headers we're looking for
            logging.debug(f"Looking for transaction headers: {transaction_section_headers}")
            
            # Add more BBVA-specific headers
            if bank_type and bank_type.lower() == 'bbva':
                transaction_section_headers.extend([
                    r'(?:FECHA DE OPERACIÓN|FECHA DE CARGO|CONCEPTO|IMPORTE)',
                    r'(?:COMPRAS|DISPOSICIONES|CARGOS)',
                    r'(?:FECHA OPERACIÓN|FECHA CARGO|DESCRIPCIÓN|IMPORTE)',
                    r'(?:CARGOS Y DISPOSICIONES)',
                    r'(?:COMPRAS Y DISPOSICIONES)'
                ])
                
            lines = text_lines
            section_start = None
            section_end = None
            
            # Find transaction section start
            for i, line in enumerate(lines):
                for header in transaction_section_headers:
                    if re.search(header, line, re.IGNORECASE):
                        section_start = i + 1  # Start after the header
                        logging.debug(f"Found transaction section start at line {i}: {line}")
                        break
                if section_start is not None:
                    break
            if section_start is None:
                logging.warning("Could not find transaction section in statement")
                return []
                
            if section_end is None:
                # If we couldn't find the end, use the end of the text
                section_end = len(lines)
                logging.debug("Could not find transaction section end, using end of text")
                
            # If we couldn't find the start, we can't extract transactions
            if section_start is None:
                logging.warning("Could not find transaction section start")
                # For BBVA, try a different approach - look for date patterns directly
                if bank_type and bank_type.lower() == 'bbva':
                    logging.info("Trying alternative approach for BBVA - searching for date patterns directly")
                    transaction_section = text
                else:
                    return []
            else:
                # Extract the transaction section
                transaction_section = '\n'.join(lines[section_start:section_end])
                
            logging.debug(f"Transaction section length: {len(transaction_section)} characters")
            
            # For debugging, log a sample of the transaction section
            if transaction_section:
                sample_length = min(1000, len(transaction_section))
                logging.debug(f"Transaction section sample: {transaction_section[:sample_length]}...")
            else:
                logging.warning("Transaction section is empty")
            
            # Try bank-specific patterns first if bank type is known
            if bank_type and bank_type.lower() in self.bank_transaction_patterns:
                patterns = self.bank_transaction_patterns[bank_type.lower()]
                logging.info(f"Using {len(patterns)} {bank_type} transaction patterns")
                # Log the first few patterns for debugging
                for i, pattern in enumerate(patterns[:3]):
                    logging.debug(f"Pattern {i}: {pattern}")
            else:
                patterns = self.generic_transaction_patterns
                logging.debug("Using generic transaction patterns")
                
            # Extract transactions using the patterns
            pattern_match_counts = {}
            # Extract transactions using the patterns
            pattern_match_counts = {}
            for pattern_idx, pattern in enumerate(patterns):
                matches = list(re.finditer(pattern, transaction_section, re.MULTILINE))
                pattern_match_counts[pattern_idx] = len(matches)
                logging.debug(f"Pattern {pattern_idx} matched {len(matches)} transactions")
                
                for match in matches:
                    try:
                        # Handle different pattern types
                        if (pattern_idx in [4, 5, 6]) and bank_type and bank_type.lower() == 'bbva':  
                            # BBVA specific patterns for credit card statements with date prefix in description
                            year = match.group('year')
                            description = match.group('description')
                            
                            # Determine transaction type based on pattern and sign
                            if pattern_idx == 4:  # Credit pattern (with + sign)
                                amount_str = '+$' + match.group('amount')
                                transaction_type = 'credit'
                            elif pattern_idx == 5:  # Debit pattern (with - sign)
                                amount_str = '-$' + match.group('amount')
                                transaction_type = 'debit'
                            else:  # Generic pattern (pattern_idx == 6)
                                # Check if there's a sign group and use it to determine transaction type
                                sign = match.group('sign') if 'sign' in match.groupdict() else None
                                
                                if sign == '+' or (not sign and '+' in match.string):
                                    amount_str = '+$' + match.group('amount')
                                    transaction_type = 'credit'
                                else:
                                    amount_str = '-$' + match.group('amount')
                                    transaction_type = 'debit'
                            
                            # Create a proper date using the year from the pattern
                            # For better accuracy, we'll use the statement month if available
                            # or fall back to current month
                            current_date = datetime.now()
                            
                            # Try to extract month from statement period if available
                            statement_month = current_date.month
                            if hasattr(self, 'statement_period') and self.statement_period:
                                try:
                                    if self.statement_period[0]:  # Start date of statement period
                                        statement_month = self.statement_period[0].month
                                except (AttributeError, IndexError):
                                    pass
                            
                            # Create a date string in format DD-MMM-YYYY
                            month_name = datetime(2000, statement_month, 1).strftime('%b')
                            date_str = f"{15}-{month_name}-{year}"  # Using 15th of the month as an approximation
                            date = self._parse_date(date_str)
                            
                            # Parse amount
                            amount = self._parse_amount(amount_str)
                            if amount is None:
                                logging.warning(f"Could not parse amount: {amount_str}")
                                continue
                                
                            # Clean description
                            description = description.strip()
                            if not description:
                                description = "Unknown"
                                
                            # Create transaction object
                            transaction = {
                                'date': date,
                                'transaction_date': date,  # Add transaction_date field for database compatibility
                                'description': description,
                                'amount': amount,
                                'type': transaction_type
                            }
                            
                            transactions.append(transaction)
                            logging.debug(f"Extracted transaction: {transaction}")
                            
                        elif len(match.groups()) >= 3:  # At least date, description, amount
                            if len(match.groups()) >= 4:  # Two dates pattern (BBVA style)
                                date_str = match.group(1)
                                description = match.group(3)
                                amount_str = match.group(4)
                            else:  # Standard pattern with one date
                                date_str = match.group(1)
                                description = match.group(2)
                                amount_str = match.group(3)
                                
                            # Parse date
                            date = self._parse_date(date_str)
                            if not date:
                                logging.warning(f"Could not parse date: {date_str}")
                                continue
                                
                            # Parse amount
                            amount = self._parse_amount(amount_str)
                            if amount is None:
                                logging.warning(f"Could not parse amount: {amount_str}")
                                continue
                                
                            # Clean description
                            description = description.strip()
                            if not description:
                                description = "Unknown"
                                
                            # Create transaction object
                            transaction = {
                                'date': date,
                                'transaction_date': date,  # Add transaction_date field for database compatibility
                                'description': description,
                                'amount': amount,
                                'type': 'debit' if amount < 0 else 'credit'
                            }
                            
                            transactions.append(transaction)
                            logging.debug(f"Extracted transaction: {transaction}")
                        else:
                            logging.warning(f"Pattern match doesn't have enough groups: {match.groups()}")
                    except Exception as e:
                        logging.error(f"Error processing match: {str(e)}")
            # Log transaction count
            logging.info(f"Extracted {len(transactions)} transactions using standardized format")
            return transactions
            
        except Exception as e:
            logging.error(f"Error in _extract_standardized_transactions: {str(e)}")
            return []
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object with enhanced support for Mexican formats"""
        if not date_str:
            return None
            
        try:
            # Clean the date string
            date_str = date_str.strip()
            date_str = re.sub(r'\s+', ' ', date_str)  # Normalize whitespace
            
            # Handle Spanish month abbreviations
            spanish_months = {
                'ene': 'jan', 'feb': 'feb', 'mar': 'mar', 'abr': 'apr',
                'may': 'may', 'jun': 'jun', 'jul': 'jul', 'ago': 'aug',
                'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dic': 'dec'
            }
            
            for sp_month, en_month in spanish_months.items():
                date_str = re.sub(fr'\b{sp_month}\b', en_month, date_str, flags=re.IGNORECASE)
                
            # Try parsing with dateutil
            return dateutil.parser.parse(date_str, dayfirst=True)  # Mexican dates are day-first
        except Exception as e:
            logging.warning(f"Error parsing date '{date_str}': {str(e)}")
            return None
            
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float with support for Mexican currency format"""
        if not amount_str:
            return None
            
        try:
            # Clean the amount string
            amount_str = amount_str.strip()
            
            # Check if it's a credit (positive) or debit (negative) amount
            is_negative = '-' in amount_str
            is_positive = '+' in amount_str
            
            # Remove currency symbols, commas and spaces
            amount_str = re.sub(r'[\$,\s]', '', amount_str)
            
            # Remove + and - signs for parsing
            amount_str = amount_str.replace('+', '').replace('-', '')
            
            # Parse as float
            amount = float(amount_str)
            
            # Apply sign based on context
            if is_negative:
                amount = -amount
            elif is_positive:
                # Explicitly marked as positive
                pass
            # If neither + nor - is present, assume it's a debit (negative) for credit card statements
            # This is a common convention in Mexican credit card statements
            elif not is_positive and not is_negative:
                # For BBVA, charges are shown as positive but are debits
                amount = -amount
                
            return amount
        except Exception as e:
            logging.warning(f"Error parsing amount '{amount_str}': {str(e)}")
            return None
            
    def _extract_summary_info(self, text: str, bank_type: str = None) -> Dict[str, Any]:
        """Extract summary information from statement text"""
        summary = {}
        
        try:
            # Extract payment due date
            payment_due_patterns = [
                r'(?:FECHA\s+(?:DE\s+)?(?:PAGO|VENCIMIENTO|CORTE))\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:PAGAR\s+ANTES\s+DE|PAGAR\s+ANTES\s+DEL)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:FECHA\s+LÍMITE\s+DE\s+PAGO)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ]
            
            for pattern in payment_due_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    due_date_str = match.group(1)
                    due_date = self._parse_date(due_date_str)
                    if due_date:
                        summary['payment_due_date'] = due_date
                        break
            
            # Extract minimum payment
            min_payment_patterns = [
                r'(?:PAGO\s+MÍNIMO)\s*:?\s*\$?\s*([\d,]+\.\d{2})',
                r'(?:MÍNIMO\s+A\s+PAGAR)\s*:?\s*\$?\s*([\d,]+\.\d{2})'
            ]
            
            for pattern in min_payment_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    min_payment_str = match.group(1)
                    min_payment = self._parse_amount('$' + min_payment_str)
                    if min_payment is not None:
                        summary['minimum_payment'] = min_payment
                        break
            
            # Extract total balance
            balance_patterns = [
                r'(?:SALDO\s+ACTUAL|SALDO\s+NUEVO)\s*:?\s*\$?\s*([\d,]+\.\d{2})',
                r'(?:SALDO\s+AL\s+CORTE)\s*:?\s*\$?\s*([\d,]+\.\d{2})',
                r'(?:TOTAL\s+A\s+PAGAR)\s*:?\s*\$?\s*([\d,]+\.\d{2})'
            ]
            
            for pattern in balance_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    balance_str = match.group(1)
                    balance = self._parse_amount('$' + balance_str)
                    if balance is not None:
                        summary['total_balance'] = balance
                        break
            
            # Extract credit limit
            limit_patterns = [
                r'(?:LÍNEA\s+DE\s+CRÉDITO|LÍMITE\s+DE\s+CRÉDITO)\s*:?\s*\$?\s*([\d,]+\.\d{2})',
                r'(?:CRÉDITO\s+DISPONIBLE)\s*:?\s*\$?\s*([\d,]+\.\d{2})'
            ]
            
            for pattern in limit_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    limit_str = match.group(1)
                    limit = self._parse_amount('$' + limit_str)
                    if limit is not None:
                        summary['credit_limit'] = limit
                        break
                        
            return summary
            
        except Exception as e:
            logging.error(f"Error extracting summary info: {str(e)}")
            return {}
            
    def _extract_statement_period_fallback(self, text: str, bank_type: str = None) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Fallback method to extract statement period by finding all dates in text"""
        try:
            # First try bank-specific patterns for BBVA
            if bank_type and bank_type.lower() == 'bbva':
                # BBVA specific patterns for statement period
                bbva_patterns = [
                    # Standard BBVA period format
                    r'Periodo:\s*(\d{2}-\w{3}-\d{4})\s*al\s*(\d{2}-\w{3}-\d{4})',
                    # Alternative format with "Del" and "al"
                    r'Del\s*(\d{2}-\w{3}-\d{4})\s*al\s*(\d{2}-\w{3}-\d{4})',
                    # Format with slashes
                    r'Periodo:\s*(\d{1,2}/\d{1,2}/\d{4})\s*al\s*(\d{1,2}/\d{1,2}/\d{4})',
                    # Format with month name
                    r'Periodo:\s*(\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4})\s*al\s*(\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4})'
                ]
                
                for pattern in bbva_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        start_date = self._parse_date(match.group(1))
                        end_date = self._parse_date(match.group(2))
                        if start_date and end_date:
                            logging.info(f"Extracted BBVA statement period: {start_date} to {end_date}")
                            return start_date, end_date
                
                # Look for year in transaction lines to determine statement year
                year_pattern = r'-(?P<year>\d{4})\s+(?P<description>.+?)\s+[\+\-]\s+\$'
                year_matches = list(re.finditer(year_pattern, text))
                if year_matches:
                    # Get the most common year from transaction lines
                    years = [match.group('year') for match in year_matches]
                    if years:
                        # Find most common year
                        from collections import Counter
                        year_counts = Counter(years)
                        most_common_year = int(year_counts.most_common(1)[0][0])
                        
                        # Look for month indicators in the text
                        month_patterns = [
                            r'(?:ESTADO\s+DE\s+CUENTA|CORTE)\s+(?:DEL\s+MES\s+DE|MES)\s+([A-Za-z]+)',
                            r'(?:ESTADO\s+DE\s+CUENTA|CORTE)\s+([A-Za-z]+)'
                        ]
                        
                        for pattern in month_patterns:
                            month_match = re.search(pattern, text, re.IGNORECASE)
                            if month_match:
                                month_name = month_match.group(1).lower()
                                # Convert Spanish month name to number
                                month_map = {
                                    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                                    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                                    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
                                    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
                                    'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
                                }
                                
                                for key, month_num in month_map.items():
                                    if key in month_name:
                                        # Create approximate statement period
                                        start_date = datetime(most_common_year, month_num, 1)
                                        # End date is last day of month
                                        if month_num == 12:
                                            end_date = datetime(most_common_year, 12, 31)
                                        else:
                                            end_date = datetime(most_common_year, month_num + 1, 1)
                                        
                                        logging.info(f"Created approximate BBVA statement period: {start_date} to {end_date}")
                                        return start_date, end_date
            
            # Generic fallback - find all dates in the text
            date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}[/-]\w{3}[/-]\d{2,4})\b'
            dates = re.findall(date_pattern, text)
            
            parsed_dates = []
            for date_str in dates:
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    parsed_dates.append(parsed_date)
                
            if parsed_dates:
                parsed_dates.sort()
                return parsed_dates[0], parsed_dates[-1]
        except Exception as e:
            logging.warning(f"Error in statement period extraction: {e}")
                
        return None, None
