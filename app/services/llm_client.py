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

    def invoke(self, messages, max_retries=3):
        """Send chat messages to the model and return the assistant's response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            max_retries: Maximum number of retry attempts on failure.
            
        Returns:
            str: The model's response text.
            
        Raises:
            RuntimeError: If the LLM client is not available or all retries fail.
        """
        if not self.is_available():
            raise RuntimeError("LLMClient not available")
            
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                # Get the content from the response
                content = getattr(response, "content", str(response))
                
                # Log the response for debugging
                logger.debug("LLM response (attempt %d/%d): %s", 
                           attempt + 1, max_retries, content)
                
                return content
                
            except Exception as exc:
                last_exception = exc
                wait_time = (attempt + 1) * 2  # Exponential backoff
                logger.warning(
                    "LLM invocation failed (attempt %d/%d): %s. Retrying in %ds...",
                    attempt + 1, max_retries, str(exc), wait_time
                )
                import time
                time.sleep(wait_time)
        
        # If we get here, all retries failed
        error_msg = f"LLM invocation failed after {max_retries} attempts"
        logger.error("%s: %s", error_msg, str(last_exception), exc_info=True)
        raise RuntimeError(f"{error_msg}: {str(last_exception)}")


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
