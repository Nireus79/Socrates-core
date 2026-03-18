"""
Standard API response format for Socratic libraries.

All API responses follow a consistent structure with status and optional data.
"""

from typing import Any, Dict, Optional


class APIResponse:
    """Standard API response wrapper."""

    def __init__(self, status: str, message: str = "", data: Optional[Dict[str, Any]] = None):
        """
        Initialize API response.

        Args:
            status: Response status ('success', 'error', 'info', etc.)
            message: Optional message text
            data: Optional response data
        """
        self.status = status
        self.message = message
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        response: Dict[str, Any] = {"status": self.status}
        if self.message:
            response["message"] = self.message
        if self.data:
            response["data"] = self.data
        return response

    @staticmethod
    def success(message: str = "", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create success response."""
        response: Dict[str, Any] = {"status": "success"}
        if message:
            response["message"] = message
        if data:
            response["data"] = data
        return response

    @staticmethod
    def error(message: str) -> Dict[str, Any]:
        """Create error response."""
        return {"status": "error", "message": message}

    @staticmethod
    def info(message: str) -> Dict[str, Any]:
        """Create info response."""
        return {"status": "info", "message": message}
