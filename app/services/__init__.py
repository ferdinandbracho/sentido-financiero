"""
StatementSense Services Module

This module provides easy access to all service classes and functions
used throughout the StatementSense application.
"""

# Import service instances for easy access
from .pdf_parser import pdf_processor
from .mexican_parser import mexican_parser
from .ocr_table_parser import ocr_table_parser
from .table_extractor import table_extractor

# Import service classes for type hints and direct instantiation
from .pdf_parser import PDFProcessor
from .mexican_parser import MexicanStatementParser
from .ocr_table_parser import OCRTableParser
from .table_extractor import TableExtractor
from .llm_client import LLMClient

__all__ = [
    # Service instances (ready to use)
    "pdf_processor",
    "mexican_parser", 
    "ocr_table_parser",
    "table_extractor",
    
    # Service classes (for type hints and instantiation)
    "PDFProcessor",
    "MexicanStatementParser",
    "OCRTableParser", 
    "TableExtractor",
    "LLMClient",
]