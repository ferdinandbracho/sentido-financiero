"""
Mexican Credit Card Statement Parser

This module implements template-based parsing for Mexican credit card statements
following the CONDUSEF government regulation format. All Mexican banks must
follow this standardized format, making template parsing highly reliable.

Author: StatementSense
Created: June 2025
"""

import re
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple

from app.config import settings

from .llm_client import LLMClient

# Initialize logger using settings
logger = settings.get_logger(__name__)

# Merchant categorization rules for Mexican transactions
# Format: {"exact_match": {}, "pattern_match": {}, "contains_match": {}}


# Mexican Statement Patterns - Based on CONDUSEF Regulation
MEXICAN_PATTERNS = {
    # Payment Patterns
    "payment_section": r"TU PAGO REQUERIDO ESTE PERIODO",
    "period_start": r"Periodo:\s*(?:Del\s+)?(\d{1,2}-\w{3}-\d{4})",
    "period_end": (
        r"(?:Del\s+\d{1,2}-\w{3}-\d{4}\s+)?"
        r"al\s+(\d{1,2}-\w{3}-\d{4})"
    ),
    "cut_date": r"Fecha de corte:\s*(\d{1,2}-\w{3}-\d{4})",
    "due_date": r"Fecha límite de pago:\s*\d*\s*([^\n]+?)(?:\n|$)",
    "pay_no_interest": (
        r"Pago para no generar intereses:\s*\d*\s*\$?([\d,]+\.?\d*)"
    ),
    "minimum_payment": (
        r"Pago mínimo(?: \+ compras y cargo diferidos a meses)?:"
        r"\s*\d*\s*\$?([\d,]+\.?\d*)"
    ),
    # Balance Section Patterns
    "previous_balance": r"Adeudo del periodo anterior\s*[\=\+\-]?\s*\$?([\d,]+\.?\d*)",
    "total_charges": r"Cargos regulares.*?\+\s*\$?([\d,]+\.?\d*)",
    "total_payments": r"Pagos y abonos.*?\-\s*\$?([\d,]+\.?\d*)",
    "credit_limit": r"Límite de crédito:\s*\$?([\d,]+\.?\d*)",
    "available_credit": r"Crédito disponible:\s*\$?([\d,]+\.?\d*)",
    "total_balance": r"Saldo deudor total:\s*\d*\s*\$?([\d,]+\.?\d*)",
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
    # Exact Match Rules (Highest Priority) - For specific, unambiguous merchant names
    "exact_match": {
        # Supermarkets & Groceries
        "OXXO": "alimentacion",
        "WALMART": "alimentacion",
        "SORIANA": "alimentacion",
        "CHEDRAUI": "alimentacion",
        "HEB": "alimentacion",
        "LA COMER": "alimentacion",
        "SUPERAMA": "alimentacion",  # Now part of Walmart Express
        "WALMART EXPRESS": "alimentacion",
        "BODEGA AURRERA": "alimentacion",
        "COSTCO": "alimentacion",  # Often mixed, but primarily groceries
        "SAMS CLUB": "alimentacion",  # Similar to Costco
        "FRESKO": "alimentacion",
        "CITY MARKET": "alimentacion",
        "ALSUPER": "alimentacion",
        "CALIMAX": "alimentacion",
        "LEY": "alimentacion",
        "SMART & FINAL": "alimentacion",
        # Convenience Stores
        "7-ELEVEN": "alimentacion",  # Often snacks/drinks
        "CIRCLE K": "alimentacion",
        "EXTRA": "alimentacion",
        "GO MART": "alimentacion",
        # Department Stores & Retail
        "LIVERPOOL": "ropa",  # Sells more than clothes, but a common category
        "PALACIO DE HIERRO": "ropa",  # Similar to Liverpool
        "SEARS": "otros",  # General merchandise
        "SUBURBIA": "ropa",
        "COPPEL": "otros",  # General, often with credit
        "ELEKTRA": "otros",  # General, electronics, credit
        "SANBORNS": "alimentacion",  # Restaurant and retail mix
        # Fashion & Clothing
        "ZARA": "ropa",
        "BERSHKA": "ropa",
        "PULL&BEAR": "ropa",
        "STRADIVARIUS": "ropa",
        "H&M": "ropa",
        "OLD NAVY": "ropa",
        "GAP": "ropa",
        "C&A": "ropa",
        "DOROTHY GAYNOR": "ropa",
        "JULIO": "ropa",
        "MASSIMO DUTTI": "ropa",
        # Health & Pharmacy
        "FARMACIAS GUADALAJARA": "salud",
        "FARMACIA DEL AHORRO": "salud",
        "FARMACIAS BENAVIDES": "salud",
        "FARMACIAS SAN PABLO": "salud",
        "FARMACIAS SIMILARES": "salud",
        # Gas Stations
        "PEMEX": "gasolineras",
        "BP": "gasolineras",
        "SHELL": "gasolineras",
        "G500": "gasolineras",
        "MOBIL": "gasolineras",
        "REPSOL": "gasolineras",
        "ORZAN": "gasolineras",
        "PETRO SEVEN": "gasolineras",
        # Restaurants & Fast Food
        "STARBUCKS": "alimentacion",
        "MCDONALDS": "alimentacion",
        "BURGER KING": "alimentacion",
        "KFC": "alimentacion",
        "DOMINOS PIZZA": "alimentacion",
        "PIZZA HUT": "alimentacion",
        "SUBWAY": "alimentacion",
        "VIPS": "alimentacion",
        "TOKS": "alimentacion",
        "EL GLOBO": "alimentacion",  # Bakery
        "LA CASA DE TOÑO": "alimentacion",
        "ITALIANNIS": "alimentacion",
        "CHILIS": "alimentacion",
        "P.F. CHANGS": "alimentacion",
        # Transportation
        "UBER": "transporte",
        "DIDI": "transporte",
        "CABIFY": "transporte",
        "ADO": "transporte",  # Bus line
        "ETN": "transporte",  # Bus line
        "PRIMERA PLUS": "transporte",  # Bus line
        "VIVA AEROBUS": "transporte",
        "AEROMEXICO": "transporte",
        "VOLARIS": "transporte",
        "METRO CDMX": "transporte",  # If card recharges appear
        "METROBUS CDMX": "transporte",
        # Entertainment
        "CINEPOLIS": "entretenimiento",
        "CINEMEX": "entretenimiento",
        "TICKETMASTER": "entretenimiento",
        "OCESA": "entretenimiento",
        "SIX FLAGS": "entretenimiento",
        "KIDZANIA": "entretenimiento",
        # Services (Online & Utilities)
        "NETFLIX": "servicios",
        "SPOTIFY": "servicios",
        "AMAZON PRIME VIDEO": "servicios",
        "HBO MAX": "servicios",  # or MAX
        "MAX": "servicios",
        "DISNEY PLUS": "servicios",
        "APPLE.COM/BILL": "servicios",  # Apple services
        "GOOGLE SERVICES": "servicios",
        "CFE": "servicios",  # Electricity
        "TELMEX": "servicios",  # Phone/Internet
        "TOTALPLAY": "servicios",
        "IZZI": "servicios",
        "MEGACABLE": "servicios",
        "SKY": "servicios",  # Satellite TV
        "TELCEL": "servicios",  # Mobile phone
        "AT&T": "servicios",  # Mobile phone
        "MOVISTAR": "servicios",  # Mobile phone
        "SACMEX": "servicios",  # Water in CDMX
        "GAS NATURAL": "servicios",  # e.g., Naturgy, Fenosa
        # Home & Electronics
        "HOME DEPOT": "otros",  # Home improvement
        "LOWES": "otros",
        "RADIOSHACK": "otros",  # Electronics
        "BEST BUY": "otros",  # Electronics
        "STEREN": "otros",
        # Education
        "UDEMY": "educacion",
        "COURSERA": "educacion",
        "PLATZI": "educacion",
        # Others
        "MERCADO LIBRE": "otros",  # Marketplace
        "AMAZON": "otros",  # Marketplace
        "PAYPAL": "otros",  # Payment proc.
        "CLIP": "otros",  # Payment proc.
        "SR PAGO": "otros",  # Payment proc.
        "CONEKTA": "otros",  # Payment processor
    },
    # Pattern Match Rules (Medium Priority) - For more general terms or variations
    "pattern_match": {
        # Food & Restaurants
        r"\b(REST|RESTAURANT|RESTAURANTE|COMIDA|ALIMENTO|COCINA|BISTRO|CAFE|CAFETERIA)\b": "alimentacion",
        r"\b(SUPERMERCADO|SUPER MARKET|MINISUPER|ABARROTES|TIENDA DE CONVENIENCIA)\b": "alimentacion",
        r"\b(PANADERIA|PASTELERIA|DULCERIA)\b": "alimentacion",
        r"\b(CARNICERIA|PESCADERIA|VERDULERIA)\b": "alimentacion",
        # Gas & Auto
        r"\b(GAS|GASOLINERA|ESTACION DE SERVICIO|PEMEX|SHELL|BP|MOBIL|REPSOL)\b": "gasolineras",
        r"\b(AUTOZONE|REFACCIONARIA|TALLER MECANICO|LLANTAS)\b": "transporte",  # Car maintenance
        r"\b(ESTACIONAMIENTO|PENSION|PARQUIMETRO)\b": "transporte",
        # Health
        r"\b(FARM|FARMACIA|BOTICA)\b": "salud",
        r"\b(DR|DRA|DOCTOR|DOCTORA|MEDICO|CONSULTORIO)\s+\w+": "salud",  # Matches "DR. PEREZ"
        r"\b(HOSPITAL|CLINICA|SANATORIO|LABORATORIO|ANALISIS CLINICOS|SALUD)\b": "salud",
        r"\b(DENTAL|DENTISTA|ODONTOLOGO)\b": "salud",
        r"\b(OPTICA|OCULISTA)\b": "salud",
        r"\b(VETERINARI[OA])\b": "salud",  # Pet health
        # Transportation
        r"\b(UBER|DIDI|CABIFY|TAXI|TRANSPORTE|PASAJES|PEAJE|CASETA)\b": "transporte",
        r"\b(AEROLINEA|VUELO|AEROPUERTO|BOLETO DE AVION)\b": "transporte",
        r"\b(AUTOBUS|CAMION|TERMINAL DE AUTOBUSES)\b": "transporte",
        # Entertainment
        r"\b(CINE|CINEMA|TEATRO|CONCIERTO|EVENTO|BOLETO|ENTRETENIMIENTO)\b": "entretenimiento",
        r"\b(BAR|CANTINA|CLUB NOCTURNO|ANTRO)\b": "entretenimiento",
        r"\b(VIDEOJUEGOS|GAMING|STEAM|XBOX|PLAYSTATION)\b": "entretenimiento",
        r"\b(MUSEO|GALERIA)\b": "entretenimiento",
        # Shopping & Retail
        r"\b(TIENDA|BOUTIQUE|ZAPATERIA|JOYERIA|REGALOS|PAPELERIA)\b": "ropa",  # General shopping, default to ropa/otros
        r"\b(LIBRERIA)\b": "educacion",  # Or "otros"
        r"\b(JUGUETERIA)\b": "otros",
        # Services & Utilities
        r"\b(LUZ|ELECTRICIDAD|CFE)\b": "servicios",
        r"\b(AGUA|SAPAL|SACM)\b": "servicios",
        r"\b(TELEFONO|INTERNET|CABLE|WIFI)\b": "servicios",
        r"\b(GASOLINERA)\b": "gasolineras",  # Duplicate for safety, covered by GAS too
        r"\b(GOBIERNO|IMPUESTO|TENENCIA|PREDIAL|SAT|TESORERIA)\b": "servicios",  # Government payments
        # Education
        r"\b(GYM|GIMNASIO|FITNESS|DEPORTE|SPORT)\b": "salud",  # Or "entretenimiento"
        r"\b(HOTEL|MOTEL|HOSTAL|ALOJAMIENTO|AIRBNB)\b": "otros",  # Travel accommodation
        r"\b(UNIVERSIDAD|COLEGIO|ESCUELA|INSTITUTO|CAPACITACION|CURSO)\b": "educacion",
        r"\b(COLEGIATURA|INSCRIPCION)\b": "educacion",
        # Financial
        r"\b(SEGURO|ASEGURADORA|POLIZA|GNP|AXA|METLIFE|QUALITAS)\b": "seguros",
        r"\b(TRANSFERENCIA|SPEI|DEPOSITO|ENVIO)\b": "transferencias",
        r"\b(INTERES|INTERESES|COMISION|CARGO|IVA)\b": "intereses_comisiones",
        r"\b(RETIRO|DISPOSICION DE EFECTIVO|CAJERO|ATM)\b": "transferencias",  # Cash withdrawal
        r"\b(AFORE|PENSION)\b": "otros",  # Savings/Retirement
        # Home
        r"\b(MUEBLERIA|DECORACION|CASA)\b": "otros",
        r"\b(LAVANDERIA|TINTORERIA)\b": "servicios",
        r"\b(FERRETERIA|TLAPALERIA)\b": "otros",
    },
    # Contains Match Rules (Lower Priority) - For keywords that might appear in broader descriptions
    "contains_match": {
        # Food keywords
        "TACO": "alimentacion",
        "PIZZA": "alimentacion",
        "SUSHI": "alimentacion",
        "HAMBURGUESA": "alimentacion",
        "CAFE": "alimentacion",  # Covered by pattern, but good for "contains" too
        "HELADO": "alimentacion",
        "POSTRE": "alimentacion",
        "VINO": "alimentacion",  # Could be "entretenimiento" if from a bar
        "CERVEZA": "alimentacion",  # Same as above
        # General Retail/Service keywords
        "MODA": "ropa",
        "LIBRO": "educacion",
        "FLORES": "otros",
        "VIAJE": "transporte",
        "CONSULTA": "salud",
        "SERVICIO": "servicios",  # Very generic, use with caution
        "COMPRA EN LINEA": "otros",  # Generic online purchase
        "ONLINE": "otros",
        "DIGITAL": "servicios",
        "APP": "servicios",
        "SUSCRIPCION": "servicios",
    },
}


class MexicanStatementParser:
    """Parser for Mexican bank statements.

    This parser handles the specific format of Mexican bank statements,
    including transaction details, dates, and amounts in MXN.

    Attributes:
        logger: Logger instance for the parser
        llm_cache: Cache for LLM categorization results
        llm_processed: Set of already processed descriptions
    """

    def __init__(self):
        """Initialize the Mexican statement parser with a logger and caches."""
        self.logger = logger
        self.llm_cache: Dict[str, str] = {}
        self.llm_processed: Set[str] = set()
        self.llm_client = LLMClient(
            api_key=settings.OPENAI_API_KEY, model_name=settings.OPENAI_MODEL
        )

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
            payment_info["due_date"] = self.parse_mexican_date(
                due_date_match.group(1)
            )
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

    def _categorize_with_llm(self, description: str) -> str:
        """Categorize a transaction description using the LLMClient (Langchain).

        Args:
            description: The transaction description to categorize.

        Returns:
            str: The category name or 'otros' if categorization fails.
        """
        if not self.llm_client.is_available():
            self.logger.debug(
                "LLMClient not available, LLM categorization skipped for: '%s'",
                description,
            )
            return "otros"

        cache_key = description.strip().upper()

        # Check cache first
        if cache_key in self.llm_cache:
            return self.llm_cache[cache_key]

        # Avoid re-processing failed LLM calls
        if cache_key in self.llm_processed:
            self.logger.debug(
                "Desc '%s' already processed by LLM (failed?), using 'otros'",
                description,
            )
            return "otros"

        try:
            valid_categories = list(
                set(MEXICAN_MERCHANT_RULES["exact_match"].values())
            )

            from langchain_core.prompts import ChatPromptTemplate

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Categorize transactions. Use one from: {categories}. "
                        "Else: 'otros'.",
                    ),
                    ("user", "Categorize this transaction: {description}"),
                ]
            )

            category_list_str = ", ".join(sorted(valid_categories))
            messages = prompt.format_messages(
                categories=category_list_str, description=description
            )
            response_text = self.llm_client.invoke(messages)
            category = response_text.strip().lower()

            # Cache the result whether successful or 'otros' from LLMClient
            self.llm_cache[cache_key] = category
            self.llm_processed.add(cache_key)  # Mark as processed

            if category != "otros":
                self.logger.debug(
                    "LLM (Langchain) categorized '%s' as '%s'",
                    description,
                    category,
                )
            else:
                self.logger.debug(
                    "LLM (Langchain) could not categorize '%s', returned 'otros'",
                    description,
                )
            return category

        except (
            Exception
        ) as e:  # Should ideally be caught within LLMClient, but as a safeguard
            self.logger.error(
                "Unexpected error during LLM categorization for '%s': %s",
                description,
                e,
                exc_info=True,
            )
            self.llm_processed.add(cache_key)
            return "otros"

    @lru_cache(maxsize=1000)
    def categorize_mexican_transaction(self, description: str) -> Optional[str]:
        """Categorize transaction using a multi-tier approach with LLM
        fallback.

        Tiers:
        1. Exact merchant name matches (fastest)
        2. Regex pattern matches (fast)
        3. Contains keyword matches (slower)
        # 4. LLM-based categorization (slowest, if enabled & no match)
        """
        if not description or not description.strip():
            return None

        description_upper = description.upper()
        # Tier 1: Exact matches (fastest)
        for merchant, category in MEXICAN_MERCHANT_RULES["exact_match"].items():
            if merchant in description_upper:
                return category

        # Tier 2: Pattern matches (fast)
        for pattern, category in MEXICAN_MERCHANT_RULES[
            "pattern_match"
        ].items():
            if re.search(pattern, description_upper):
                return category

        # Tier 3: Contains matches (slower)
        for keyword, category in MEXICAN_MERCHANT_RULES[
            "contains_match"
        ].items():
            if keyword in description_upper:
                return category

        # No rule matched
        return None

    def _categorize_batch_with_llm(self, descriptions: List[str]) -> Dict[str, str]:
        """Categorize a list of descriptions in a single LLM call.

        The method sends all unique descriptions to the LLM and expects a JSON
        object as response mapping each description to a category.
        """
        if not self.llm_client.is_available() or not descriptions:
            return {}

        # Build list of valid categories from rule set.
        valid_categories: List[str] = list(
            {cat for cat in MEXICAN_MERCHANT_RULES["exact_match"].values()}
        )
        category_list = ", ".join(sorted(valid_categories))

        # Prepare prompts
        system_content = (
            "You are a helpful financial assistant. Categorize each bank "
            "transaction description using ONE of the following categories: "
            f"{category_list}. If none apply, reply with 'otros'. "
            "Return ONLY a single valid JSON object mapping each description "
            "to its category. Do not wrap the JSON in markdown or add any keys "
            "other than the descriptions."
        )
        user_content = "Descriptions: " + json.dumps(descriptions, ensure_ascii=False)

        try:
            from langchain_core.prompts import ChatPromptTemplate

            prompt = ChatPromptTemplate.from_messages(
                [("system", system_content), ("user", user_content)]
            )
            messages = prompt.format_messages()
            response = self.llm_client.invoke(messages)
            
            # Clean and validate the response
            response = response.strip()
            
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                self.logger.error("LLM batch response missing JSON: %s", response)
                return {}
                
            json_str = json_match.group(0)
            
            # Try to parse the JSON
            try:
                parsed = json.loads(json_str)
                if not isinstance(parsed, dict):
                    raise ValueError("Response is not a JSON object")
                    
                result: Dict[str, str] = {}
                for desc, cat in parsed.items():
                    if not isinstance(desc, str) or not isinstance(cat, str):
                        continue
                        
                    cat_lower = cat.lower().strip()
                    if cat_lower not in valid_categories:
                        cat_lower = "otros"
                    result[desc] = cat_lower
                
                return result
                
            except json.JSONDecodeError as e:
                self.logger.error("Failed to parse LLM response as JSON: %s", e)
                self.logger.debug("Raw response: %s", response)
                return {}
                
        except Exception as exc:
            self.logger.error("Error in batch LLM categorization: %s", exc, exc_info=True)
            return {}

    def validate_extraction(self, extracted_data: Dict) -> Dict[str, Any]:
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
    
    def _validate_mexican_format(self, text: str) -> bool:
        """
        Validate if text follows Mexican CONDUSEF format.
        Uses flexible validation for OCR-extracted content.
        """
        # Traditional validation (exact text match)
        if re.search(MEXICAN_PATTERNS["payment_section"], text):
            self.logger.debug("Found traditional CONDUSEF format indicator")
            return True
        
        # Flexible validation for OCR-extracted table format
        text_upper = text.upper()
        
        # CONDUSEF structure indicators
        condusef_indicators = [
            "TU PAGO REQUERIDO",  # Partial match of payment section
            "DESGLOSE DE MOVIMIENTOS",  # Transaction section
            "PAGO PARA NO GENERAR INTERESES",  # Payment to avoid interest
            "CARGOS, ABONOS Y COMPRAS REGULARES",  # Regular charges table
            "SALDO DEUDOR TOTAL",  # Total debt
            "LÍMITE DE CRÉDITO",  # Credit limit
            "CRÉDITO DISPONIBLE"  # Available credit
        ]
        
        # Mexican bank indicators
        mexican_banks = [
            "SANTANDER", "BBVA", "BANAMEX", "BANORTE", "HSBC", 
            "SCOTIABANK", "CITIBANAMEX", "INBURSA", "BANCO AZTECA"
        ]
        
        # Credit card terminology
        credit_terms = [
            "TARJETA DE CRÉDITO", "TARJETA DE CREDITO", "ESTADO DE CUENTA",
            "FECHA DE CORTE", "PAGO MÍNIMO", "PAGO MINIMO"
        ]
        
        # Mexican date patterns (DD-MMM-YYYY format)
        mexican_date_patterns = [
            r"\d{1,2}-(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-\d{4}",
            r"(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-\d{1,2}",
        ]
        
        # Mexican amount patterns (peso format)
        mexican_amount_patterns = [
            r"\$\s*[\d,]+\.?\d*",  # $1,234.56
            r"[\d,]+\.\d{2}",      # 1,234.56
        ]
        
        # Score different types of indicators
        condusef_score = sum(1 for indicator in condusef_indicators if indicator in text_upper)
        bank_score = sum(1 for bank in mexican_banks if bank in text_upper)
        credit_score = sum(1 for term in credit_terms if term in text_upper)
        
        # Check for date patterns
        date_score = 0
        for pattern in mexican_date_patterns:
            if re.search(pattern, text_upper):
                date_score += 1
        
        # Check for amount patterns
        amount_score = 0
        for pattern in mexican_amount_patterns:
            if re.search(pattern, text):
                amount_score += 1
        
        # Special check for OCR table format with "DESGLOSE DE MOVIMIENTOS" header
        has_transaction_header = "DESGLOSE DE MOVIMIENTOS" in text_upper
        
        self.logger.debug(f"Mexican format validation scores - CONDUSEF: {condusef_score}, Bank: {bank_score}, Credit: {credit_score}, Date: {date_score}, Amount: {amount_score}, Transaction header: {has_transaction_header}")
        
        # Validation logic for different confidence levels
        
        # High confidence: Traditional CONDUSEF indicators
        if condusef_score >= 2:
            self.logger.debug("High confidence: Multiple CONDUSEF indicators found")
            return True
        
        # Medium confidence: Bank + credit terms + structural elements
        if bank_score >= 1 and credit_score >= 1 and (date_score >= 1 or amount_score >= 1):
            self.logger.debug("Medium confidence: Bank + credit terms + structural elements")
            return True
        
        # OCR table specific: Has transaction header (added by our table extractor)
        if has_transaction_header:
            self.logger.debug("OCR table confidence: Found transaction header")
            return True
        
        # Low confidence: Multiple structural indicators
        if (bank_score + credit_score + date_score + amount_score) >= 4:
            self.logger.debug("Low confidence: Multiple structural indicators")
            return True
        
        self.logger.debug("No sufficient Mexican format indicators found")
        return False

    def parse_statement(self, text: str) -> Dict[str, any]:
        """
        Main parsing method for Mexican credit card statements.

        Returns a structured data dictionary with all extracted information
        and confidence scores.
        """
        self.logger.info("Starting Mexican statement parsing")

        # Check if this looks like a Mexican statement
        # For OCR-extracted table format, use more flexible validation
        is_mexican_format = self._validate_mexican_format(text)
        
        if not is_mexican_format:
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

            # Categorize transactions using rule-based tiers first
            uncategorized: Set[str] = set()
            for transaction in extracted_data["transactions"]:
                cat = self.categorize_mexican_transaction(transaction["description"])
                if cat:
                    transaction["category"] = cat
                else:
                    # Mark for LLM batch processing
                    transaction["category"] = "otros"  # provisional
                    uncategorized.add(transaction["description"])

            # Batch-categorize uncategorized descriptions with the LLM
            if uncategorized:
                llm_results = self._categorize_batch_with_llm(list(uncategorized))
                if llm_results:
                    for transaction in extracted_data["transactions"]:
                        desc = transaction["description"]
                        if desc in llm_results:
                            transaction["category"] = llm_results[desc]

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
