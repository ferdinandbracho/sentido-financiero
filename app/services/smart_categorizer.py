from __future__ import annotations

from typing import Optional

import re


class SmartCategorizer:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
    ):
        """Initialize the SmartCategorizer with optional OpenAI configuration.

        Args:
            openai_api_key: Optional OpenAI API key. If not provided,
                LLM features will be disabled.
            model_name: Name of the OpenAI model to use
                (default: 'gpt-3.5-turbo').
        """
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.llm_available = bool(openai_api_key)

        if self.llm_available:
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=openai_api_key)
            except ImportError:
                self.llm_available = False

    def is_recurring(
        self, description: str, recurring_keywords: list[str]
    ) -> bool:
        """Check if transaction matches any recurring payment keywords.

        Args:
            description: Transaction description to check
            recurring_keywords: List of keywords to match against

        Returns:
            bool: True if any keyword is found in description (case-insensitive)
        """
        if not description:
            return False

        description_lower = description.lower()
        return any(
            keyword in description_lower for keyword in recurring_keywords
        )

    def _extract_merchant_name(self, description: str) -> Optional[str]:
        """Extract clean merchant name from description."""
        if not description:
            return None

        # Example: "COMPRA EN TIENDA XYZ SA DE CV" -> "TIENDA XYZ"
        name = description.upper()
        prefixes = ["COMPRA EN ", "PAGO EN ", "RETIRO EN "]
        suffixes = [" SA DE CV", " SAB DE CV", " SC", " S DE RL DE CV"]

        # Remove common prefixes/suffixes
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix) :]

        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[: -len(suffix)]

        # Remove common noise
        noise_patterns = [
            r"^(STR\*|STRIPE\s*\*|CLIP\s*MX\s*\*)",
            r"\s*;\s*Tarjeta\s+Digital.*$",
            r"\s*\d+$",  # Trailing numbers
            r"^\s*(REST|RESTAURANTE)\s+",  # Restaurant prefixes
        ]

        for pattern in noise_patterns:
            name = re.sub(pattern, "", name)

        # Extract first meaningful part (usually merchant name)
        parts = name.split()
        if parts:
            # Take first 2-3 words as merchant name
            merchant = " ".join(parts[:3]).strip()
            return merchant if len(merchant) > 2 else None

        return None
