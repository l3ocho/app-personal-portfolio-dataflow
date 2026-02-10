"""Custom exceptions for the portfolio application."""


class PortfolioError(Exception):
    """Base exception for all portfolio errors."""


class ParseError(PortfolioError):
    """PDF/CSV parsing failed."""


class ValidationError(PortfolioError):
    """Pydantic or business rule validation failed."""


class LoadError(PortfolioError):
    """Database load operation failed."""
