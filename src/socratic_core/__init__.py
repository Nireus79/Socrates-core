"""
Socratic Core - Base framework for Socratic CLI and API libraries.

Provides core functionality for building command-based CLI applications
and utilities used across the Socratic ecosystem.
"""

from socratic_core.commands.base import BaseCommand
from socratic_core.responses import APIResponse

__version__ = "0.1.0"
__author__ = "Socrates Team"
__email__ = "info@socrates-ai.dev"

__all__ = ["BaseCommand", "APIResponse"]
