"""
LLM Client Module

Provides a client for LLM interactions using Langchain.
"""

from typing import Optional

from langchain_openai import ChatOpenAI

from app.config import settings

# Initialize logger using settings
logger = settings.get_logger(__name__)


class LLMClient:
    """Client for LLM interactions using Langchain."""

    def __init__(self, api_key: Optional[str], model_name: Optional[str]):
        """Initialize the LLM client.

        Args:
            api_key: The API key for the LLM provider.
            model_name: The name of the model to use.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.llm = None

        if self.api_key and self.model_name:
            try:
                self.llm = ChatOpenAI(
                    api_key=self.api_key,
                    model=self.model_name,
                    temperature=0.1,
                    max_tokens=20,
                )
                logger.info(
                    "LLMClient initialized with model: %s",
                    self.model_name,
                )
            except Exception as e:
                logger.error(
                    "Failed to initialize ChatOpenAI: %s",
                    e,
                )
                self.llm = None  # Ensure llm is None if initialization fails
        else:
            logger.warning(
                "API key or model name not provided. LLMClient will not function."
            )

    def is_available(self) -> bool:
        """Check if the LLM client is properly configured and available."""
        return self.llm is not None

    def invoke(self, messages):
        """Send chat messages to the model and return the raw assistant text."""
        if not self.is_available():
            raise RuntimeError("LLMClient not available")
        try:
            response = self.llm.invoke(messages)
            # ChatOpenAI returns a BaseMessage; grab its content attribute if present.
            return getattr(response, "content", str(response))
        except Exception as exc:
            logger.error("LLM invocation failed: %s", exc, exc_info=True)
            raise


if __name__ == "__main__":
    import sys

    print("sys.path before imports: {}\n".format(sys.path))

    # Example Usage (requires OPENAI_API_KEY and OPENAI_MODEL in .env/settings
    if not settings.OPENAI_API_KEY:
        print(
            "Please set your OPENAI_API_KEY in a .env file or "
            "environment variable."
        )
    else:
        client = LLMClient(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
        )
        if client.is_available():
            test_description = "POINTMP*VONDYMEXICO"
            categories_fixture = [
                "alimentacion",
                "gasolineras",
                "servicios",
                "salud",
                "transporte",
                "entretenimiento",
                "ropa",
                "educacion",
                "transferencias",
                "seguros",
                "intereses_comisiones",
                "otros",
            ]

            print("\n--- Testing LLM Client ---")
            print("Test 1: Simple message")
            print("Sending: '{}'".format(test_description))
            result = client.invoke(
                [{"role": "user", "content": test_description}]
            )
            print("Response: {}".format(result))

            print("\nTest 2: Categorization prompt")
            test_description_2 = "COMPRA EN OXXO"
            print("Sending: '{}'".format(test_description_2))
            # Example of a system + user message structure
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that categorizes transactions.",
                },
                {
                    "role": "user",
                    "content": f"Categorize this transaction: {test_description_2}",
                },
            ]
            result_2 = client.invoke(messages)
            print(f"Response: {result_2}")
        else:
            print(
                "LLM Client is not available. Check API key, model name, or Langchain installation."
            )
