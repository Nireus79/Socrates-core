"""
Exception classes for Socratic Core.

Provides structured error handling across all components.
"""


class SocratesError(Exception):
    """Base exception for all Socrates errors."""

    pass


class ConfigurationError(SocratesError):
    """Raised when configuration is invalid."""

    pass


class DatabaseError(SocratesError):
    """Raised when database operations fail."""

    pass


class ValidationError(SocratesError):
    """Raised when validation fails."""

    pass


class AuthenticationError(SocratesError):
    """Raised when authentication fails."""

    pass


class APIError(SocratesError):
    """Raised when API calls fail."""

    pass


class AgentError(SocratesError):
    """Raised when agent operations fail."""

    pass


class ProjectNotFoundError(SocratesError):
    """Raised when a project is not found."""

    pass


class UserNotFoundError(SocratesError):
    """Raised when a user is not found."""

    pass
