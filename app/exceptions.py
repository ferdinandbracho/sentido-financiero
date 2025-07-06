"""
Custom exceptions for StatementSense application.

This module defines specific exception types for better error handling
and debugging throughout the application.

Author: StatementSense
Created: July 2025
"""


class StatementSenseException(Exception):
    """Base exception for all StatementSense-specific errors."""
    pass


class PDFProcessingError(StatementSenseException):
    """Raised when PDF processing fails."""
    
    def __init__(self, message: str, file_name: str = None, file_size: int = None):
        self.file_name = file_name
        self.file_size = file_size
        super().__init__(message)


class TextExtractionError(PDFProcessingError):
    """Raised when text extraction from PDF fails."""
    pass


class OCRExtractionError(PDFProcessingError):
    """Raised when OCR extraction fails."""
    pass


class ParsingError(StatementSenseException):
    """Raised when statement parsing fails."""
    
    def __init__(self, message: str, parser_type: str = None, confidence: float = None):
        self.parser_type = parser_type
        self.confidence = confidence
        super().__init__(message)


class MexicanParserError(ParsingError):
    """Raised when Mexican template parsing fails."""
    pass


class OCRTableParserError(ParsingError):
    """Raised when OCR table parsing fails."""
    pass


class ValidationError(StatementSenseException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        self.field = field
        self.value = value
        super().__init__(message)


class ConfigurationError(StatementSenseException):
    """Raised when configuration is invalid or missing."""
    pass


class DatabaseError(StatementSenseException):
    """Raised when database operations fail."""
    pass


class FileValidationError(StatementSenseException):
    """Raised when uploaded file validation fails."""
    
    def __init__(self, message: str, file_name: str = None, file_type: str = None):
        self.file_name = file_name
        self.file_type = file_type
        super().__init__(message)


class ServiceUnavailableError(StatementSenseException):
    """Raised when external services (LLM, OCR) are unavailable."""
    
    def __init__(self, message: str, service_name: str = None):
        self.service_name = service_name
        super().__init__(message)