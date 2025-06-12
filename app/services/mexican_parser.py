"""
Mexican Credit Card Statement Parser

This module implements template-based parsing for Mexican credit card statements
following the CONDUSEF government regulation format. All Mexican banks must
follow this standardized format, making template parsing highly reliable.

Author: StatementSense
Created: June 2025
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple

from app.config import settings

logger = settings.get_logger(__name__)

# Mexican Statement Patterns - Based on CONDUSEF Regulation
MEXICAN_PATTERNS = {
    # Payment Section Patterns
    "payment_section": r"TU PAGO REQUERIDO ESTE PERIODO",
    "period_start": r"Periodo:\s*(?:Del\s+)?(\d{1,2}-\w{3}-\d{4})",
    "period_end": r"(?:Del\s+\d{1,2}-\w{3}-\d{4}\s+)?al\s+(\d{1,2}-\w{3}-\d{4})",
    "cut_date": r"Fecha de corte:\s*(\d{1,2}-\w{3}-\d{4})",
    "due_date": r"Fecha límite de pago:\s*(.+?)(?:\n|$)",
    "pay_no_interest": r"Pago para no generar intereses:\s*\$?([\d,]+\.?\d*)",
    "minimum_payment": r"Pago mínimo:\s*\$?([\d,]+\.?\d*)",
    # Balance Section Patterns
    "previous_balance": r"Adeudo del periodo anterior\s*[\=\+\-]?\s*\$?([\d,]+\.?\d*)",
    "total_charges": r"Cargos regulares.*?\+\s*\$?([\d,]+\.?\d*)",
    "total_payments": r"Pagos y abonos.*?\-\s*\$?([\d,]+\.?\d*)",
    "credit_limit": r"Límite de crédito:\s*\$?([\d,]+\.?\d*)",
    "available_credit": r"Crédito disponible:\s*\$?([\d,]+\.?\d*)",
    "total_balance": r"Saldo deudor total:\s*\$?([\d,]+\.?\d*)",
    # Transaction Section Patterns
    "transaction_section": r"DESGLOSE DE MOVIMIENTOS",
    "transaction_table": r"CARGOS.*?ABONOS.*?REGULARES.*?\(NO A MESES\)",
    # Customer Info Patterns
    "card_number": r"[Nn]úmero de tarjeta:\s*(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})",
    "customer_name_pattern": r"^([A-Z\s]{10,50})\s*$",
    "bank_name": r"(BBVA|Santander|Banamex|HSBC|Scotiabank|Banorte|Citibanamex)",
    # Date and Amount Formats
    "mexican_date": r"(\d{1,2})-(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-(\d{4})",
    "mexican_amount": r"[\+\-]?\s*\$?\s*([\d,]+\.?\d*)",
}

# Mexican Month Translation Map
MEXICAN_MONTH_MAP = {
    "ENE": "01",
    "FEB": "02",
    "MAR": "03",
    "ABR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AGO": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DIC": "12",
}

# Mexican Merchant Categorization Rules
MEXICAN_MERCHANT_RULES = {
    # Exact Match Rules (Highest Priority)
    "exact_match": {
        "OXXO": "alimentacion",
        "WALMART": "alimentacion",
        "PEMEX": "gasolineras",
        "NETFLIX": "servicios",
        "UBER": "transporte",
        "LIVERPOOL": "ropa",
        "PALACIO DE HIERRO": "ropa",
        "FARMACIAS GUADALAJARA": "salud",
        "FARMACIA DEL AHORRO": "salud",
        "CINEPOLIS": "entretenimiento",
        "STARBUCKS": "alimentacion",
        "MCDONALDS": "alimentacion",
        "SUBURBIA": "ropa",
        "COPPEL": "ropa",
        "ELEKTRA": "otros",
        "SORIANA": "alimentacion",
        "CHEDRAUI": "alimentacion",
        "HEB": "alimentacion",
    },
    # Pattern Match Rules (Medium Priority)
    "pattern_match": {
        r"\b(REST|RESTAURANT|RESTAURANTE)\b": "alimentacion",
        r"\b(GAS|GASOLINERA|PEMEX|SHELL|BP)\b": "gasolineras",
        r"\b(FARM|FARMACIA)\b": "salud",
        r"\b(DR|DRA|DOCTOR|DOCTORA)\s+\w+": "salud",
        r"\b(HOSPITAL|CLINICA|MEDICAL)\b": "salud",
        r"\b(UBER|TAXI|TRANSPORTE)\b": "transporte",
        r"\b(CINE|CINEMA|TEATRO)\b": "entretenimiento",
        r"\b(GYM|GIMNASIO|FITNESS)\b": "salud",
        r"\b(HOTEL|MOTEL)\b": "otros",
        r"\b(UNIVERSITY|UNIVERSIDAD|ESCUELA)\b": "educacion",
        r"\b(SEGURO|INSURANCE)\b": "seguros",
        r"\bTRANSFERENCIA\b": "transferencias",
        r"\b(INTERES|INTEREST|COMISION)\b": "intereses_comisiones",
    },
    # Contains Match Rules (Lower Priority)
    "contains_match": {
        "TACO": "alimentacion",
        "PIZZA": "alimentacion",
        "COFFEE": "alimentacion",
        "CAFE": "alimentacion",
        "BAR": "entretenimiento",
        "CANTINA": "entretenimiento",
    },
}


class MexicanStatementParser:
    """
    Template-based parser for Mexican credit card statements following
    CONDUSEF government regulation format.
    """

    def __init__(self):
        self.logger = logger

    def parse_mexican_date(self, date_str: str) -> Optional[datetime]:
        """Convert Mexican date format (DD-MMM-YYYY) to datetime object."""
        try:
            match = re.search(
                MEXICAN_PATTERNS["mexican_date"], date_str, re.IGNORECASE
            )
            if match:
                day, month_abbr, year = match.groups()
                month = MEXICAN_MONTH_MAP.get(month_abbr.upper())
                if month:
                    return datetime.strptime(
                        f"{year}-{month}-{day.zfill(2)}", "%Y-%m-%d"
                    )
        except Exception as e:
            self.logger.warning(
                f"Failed to parse Mexican date '{date_str}': {e}"
            )
        return None

    def parse_mexican_amount(self, amount_str: str) -> Optional[Decimal]:
        """Convert Mexican amount format ($X,XXX.XX) to Decimal."""
        try:
            # Remove currency symbols and whitespace
            clean_amount = re.sub(r"[\$\s]", "", amount_str)
            # Handle negative amounts in parentheses
            is_negative = clean_amount.startswith(
                "-"
            ) or clean_amount.startswith("(")
            # Remove commas and parentheses
            clean_amount = re.sub(r"[,\(\)]", "", clean_amount).replace("-", "")

            if clean_amount:
                amount = Decimal(clean_amount)
                return -amount if is_negative else amount
        except (InvalidOperation, ValueError) as e:
            self.logger.warning(
                f"Failed to parse Mexican amount '{amount_str}': {e}"
            )
        return None

    def detect_bank(self, text: str) -> Optional[str]:
        """Detect which Mexican bank issued the statement."""
        bank_patterns = {
            "BBVA": r"BBVA|Bancomer",
            "Santander": r"Santander",
            "Banamex": r"Banamex|Citibanamex",
            "HSBC": r"HSBC",
            "Banorte": r"Banorte",
            "Scotiabank": r"Scotiabank",
        }

        for bank, pattern in bank_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return bank
        return None

    def extract_customer_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract customer information from statement."""
        info = {"customer_name": None, "card_number": None, "bank_name": None}

        # Extract bank name
        info["bank_name"] = self.detect_bank(text)

        # Extract card number
        card_match = re.search(MEXICAN_PATTERNS["card_number"], text)
        if card_match:
            info["card_number"] = card_match.group(1).replace(" ", "")

        # Extract customer name (look for lines with all caps names)
        lines = text.split("\n")
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if re.match(r"^[A-Z\s]{10,50}$", line) and len(line.split()) >= 2:
                # Likely a customer name
                info["customer_name"] = line
                break

        return info

    def extract_payment_info(self, text: str) -> Dict[str, any]:
        """Extract payment information from statement."""
        payment_info = {
            "period_start": None,
            "period_end": None,
            "cut_date": None,
            "due_date": None,
            "pay_no_interest": None,
            "minimum_payment": None,
            "confidence": 0.0,
        }

        found_fields = 0
        total_fields = 6

        # Extract period dates
        period_start_match = re.search(MEXICAN_PATTERNS["period_start"], text)
        if period_start_match:
            payment_info["period_start"] = self.parse_mexican_date(
                period_start_match.group(1)
            )
            if payment_info["period_start"]:
                found_fields += 1

        period_end_match = re.search(MEXICAN_PATTERNS["period_end"], text)
        if period_end_match:
            payment_info["period_end"] = self.parse_mexican_date(
                period_end_match.group(1)
            )
            if payment_info["period_end"]:
                found_fields += 1

        # Extract cut date
        cut_date_match = re.search(MEXICAN_PATTERNS["cut_date"], text)
        if cut_date_match:
            payment_info["cut_date"] = self.parse_mexican_date(
                cut_date_match.group(1)
            )
            if payment_info["cut_date"]:
                found_fields += 1

        # Extract due date (text format)
        due_date_match = re.search(MEXICAN_PATTERNS["due_date"], text)
        if due_date_match:
            payment_info["due_date"] = due_date_match.group(1).strip()
            found_fields += 1

        # Extract payment amounts
        pay_no_interest_match = re.search(
            MEXICAN_PATTERNS["pay_no_interest"], text
        )
        if pay_no_interest_match:
            payment_info["pay_no_interest"] = self.parse_mexican_amount(
                pay_no_interest_match.group(1)
            )
            if payment_info["pay_no_interest"] is not None:
                found_fields += 1

        minimum_payment_match = re.search(
            MEXICAN_PATTERNS["minimum_payment"], text
        )
        if minimum_payment_match:
            payment_info["minimum_payment"] = self.parse_mexican_amount(
                minimum_payment_match.group(1)
            )
            if payment_info["minimum_payment"] is not None:
                found_fields += 1

        # Calculate confidence score
        payment_info["confidence"] = found_fields / total_fields

        return payment_info

    def extract_balance_info(self, text: str) -> Dict[str, any]:
        """Extract balance information from statement."""
        balance_info = {
            "previous_balance": None,
            "total_charges": None,
            "total_payments": None,
            "credit_limit": None,
            "available_credit": None,
            "total_balance": None,
            "confidence": 0.0,
        }

        found_fields = 0
        total_fields = 6

        # Extract balance amounts
        patterns_to_extract = [
            ("previous_balance", MEXICAN_PATTERNS["previous_balance"]),
            ("total_charges", MEXICAN_PATTERNS["total_charges"]),
            ("total_payments", MEXICAN_PATTERNS["total_payments"]),
            ("credit_limit", MEXICAN_PATTERNS["credit_limit"]),
            ("available_credit", MEXICAN_PATTERNS["available_credit"]),
            ("total_balance", MEXICAN_PATTERNS["total_balance"]),
        ]

        for field_name, pattern in patterns_to_extract:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = self.parse_mexican_amount(match.group(1))
                if amount is not None:
                    balance_info[field_name] = amount
                    found_fields += 1

        # Calculate confidence score
        balance_info["confidence"] = found_fields / total_fields

        return balance_info

    def extract_transactions(self, text: str) -> Tuple[List[Dict], float]:
        """Extract transaction list from statement."""
        transactions = []
        confidence = 0.0

        # Look for transaction section
        transaction_section_match = re.search(
            MEXICAN_PATTERNS["transaction_section"], text
        )
        if not transaction_section_match:
            self.logger.warning("Transaction section not found in statement")
            return transactions, 0.0

        # Extract transaction table section
        transaction_start = transaction_section_match.end()
        transaction_text = text[
            transaction_start : transaction_start + 10000
        ]  # Limit search area

        # Pattern for transaction lines: Date Date Description Amount
        transaction_pattern = r"(\d{1,2}-\w{3}-\d{4})\s+(\d{1,2}-\w{3}-\d{4})\s+(.+?)\s+([\+\-]?\s*\$?\s*[\d,]+\.?\d*)"

        matches = re.findall(
            transaction_pattern, transaction_text, re.MULTILINE
        )

        successful_parses = 0
        for match in matches:
            try:
                operation_date_str, charge_date_str, description, amount_str = (
                    match
                )

                operation_date = self.parse_mexican_date(operation_date_str)
                charge_date = self.parse_mexican_date(charge_date_str)
                amount = self.parse_mexican_amount(amount_str)

                if operation_date and charge_date and amount is not None:
                    transaction = {
                        "operation_date": operation_date,
                        "charge_date": charge_date,
                        "description": description.strip(),
                        "amount": amount,
                        "transaction_type": "DEBIT" if amount < 0 else "CREDIT",
                    }
                    transactions.append(transaction)
                    successful_parses += 1

            except Exception as e:
                self.logger.warning(
                    f"Failed to parse transaction: {match}, error: {e}"
                )

        # Calculate confidence based on successful parsing
        if matches:
            confidence = successful_parses / len(matches)

        self.logger.info(
            f"Extracted {len(transactions)} transactions with confidence {confidence:.2f}"
        )

        return transactions, confidence

    def categorize_mexican_transaction(self, description: str) -> str:
        """Categorize transaction using Mexican merchant rules."""
        description_upper = description.upper()

        # Tier 1: Exact matches
        for merchant, category in MEXICAN_MERCHANT_RULES["exact_match"].items():
            if merchant in description_upper:
                return category

        # Tier 2: Pattern matches
        for pattern, category in MEXICAN_MERCHANT_RULES[
            "pattern_match"
        ].items():
            if re.search(pattern, description_upper):
                return category

        # Tier 3: Contains matches
        for keyword, category in MEXICAN_MERCHANT_RULES[
            "contains_match"
        ].items():
            if keyword in description_upper:
                return category

        # Default category
        return "otros"

    def validate_extraction(self, extracted_data: Dict) -> Dict[str, any]:
        """Validate extracted data for consistency and completeness."""
        validation_result = {
            "is_valid": True,
            "confidence": 0.0,
            "errors": [],
            "warnings": [],
        }

        # Check required fields
        required_fields = [
            "customer_info",
            "payment_info",
            "balance_info",
            "transactions",
        ]
        missing_fields = [
            field for field in required_fields if field not in extracted_data
        ]

        if missing_fields:
            validation_result["errors"].append(
                f"Missing required fields: {missing_fields}"
            )
            validation_result["is_valid"] = False

        # Validate individual section confidence scores
        confidence_scores = []
        for section in ["payment_info", "balance_info"]:
            if (
                section in extracted_data
                and "confidence" in extracted_data[section]
            ):
                confidence_scores.append(extracted_data[section]["confidence"])

        # Add transaction confidence
        if "transactions_confidence" in extracted_data:
            confidence_scores.append(extracted_data["transactions_confidence"])

        # Calculate overall confidence
        if confidence_scores:
            validation_result["confidence"] = sum(confidence_scores) / len(
                confidence_scores
            )

        # Validate transaction count
        if "transactions" in extracted_data:
            if len(extracted_data["transactions"]) == 0:
                validation_result["warnings"].append("No transactions found")
            elif len(extracted_data["transactions"]) > 1000:
                validation_result["warnings"].append(
                    "Unusually high transaction count"
                )

        # Set overall validity based on confidence threshold
        if validation_result["confidence"] < 0.6:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Low confidence score: {validation_result['confidence']:.2f}"
            )

        return validation_result

    def parse_statement(self, text: str) -> Dict[str, any]:
        """
        Main parsing method for Mexican credit card statements.

        Returns a structured data dictionary with all extracted information
        and confidence scores.
        """
        self.logger.info("Starting Mexican statement parsing")

        # Check if this looks like a Mexican statement
        if not re.search(MEXICAN_PATTERNS["payment_section"], text):
            self.logger.warning(
                "Statement does not appear to follow Mexican CONDUSEF format"
            )
            return {
                "success": False,
                "error": "Statement format not recognized as Mexican CONDUSEF standard",
                "confidence": 0.0,
            }

        try:
            # Extract all sections
            extracted_data = {
                "customer_info": self.extract_customer_info(text),
                "payment_info": self.extract_payment_info(text),
                "balance_info": self.extract_balance_info(text),
            }

            # Extract transactions
            transactions, transactions_confidence = self.extract_transactions(
                text
            )
            extracted_data["transactions"] = transactions
            extracted_data["transactions_confidence"] = transactions_confidence

            # Categorize transactions
            for transaction in extracted_data["transactions"]:
                transaction["category"] = self.categorize_mexican_transaction(
                    transaction["description"]
                )

            # Validate extraction
            validation_result = self.validate_extraction(extracted_data)

            # Return complete result
            return {
                "success": validation_result["is_valid"],
                "data": extracted_data,
                "validation": validation_result,
                "confidence": validation_result["confidence"],
                "extraction_method": "mexican_template",
            }

        except Exception as e:
            self.logger.error(f"Error during Mexican statement parsing: {e}")
            return {"success": False, "error": str(e), "confidence": 0.0}


# Create a singleton instance for easy import
mexican_parser = MexicanStatementParser()
