"""
Base Agent class for all Socratic libraries.

This is the foundation for all agents across the 12 Socratic libraries.
Provides unified interface for agent implementation following monolithic standards.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from socratic_core.events import EventType

if TYPE_CHECKING:
    from socratic_core.agent_orchestrator import AgentOrchestrator


class Agent(ABC):
    """
    Abstract base class for all agents in Socratic libraries.

    All agents across the 12 libraries (Socratic-agents, socratic-learning,
    Socratic-conflict, etc.) inherit from this unified base class.

    Agents are specialized components that handle different aspects of
    AI workflows and are capable of:
    - Synchronous request processing via process()
    - Asynchronous request processing via process_async()
    - Event-based logging via log()
    - Structured event emission via emit_event()
    - Knowledge gap detection via suggest_knowledge_addition()
    """

    def __init__(self, name: str, orchestrator: "AgentOrchestrator"):
        """
        Initialize an agent.

        Args:
            name: Display name for the agent
            orchestrator: Reference to the AgentOrchestrator for agent coordination
        """
        self.name = name
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(f"socratic.agents.{name}")
        self.created_at = datetime.utcnow()

    @abstractmethod
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request and return a response (synchronous).

        All subclasses must implement this method to handle their specific logic.

        Args:
            request: Dictionary containing the request parameters

        Returns:
            Dictionary containing the response data

        Example:
            >>> result = agent.process({'action': 'analyze', 'data': '...'})
            >>> if result['status'] == 'success':
            ...     print(result['data'])
        """
        pass

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request asynchronously.

        Default implementation wraps the synchronous process method using asyncio.
        Subclasses can override this to provide true async processing for I/O-bound operations.

        Args:
            request: Dictionary containing the request parameters

        Returns:
            Dictionary containing the response data
        """
        # Run sync method in thread pool to avoid blocking
        return await asyncio.to_thread(self.process, request)

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Emit a structured log event and write to logger.

        Replaces direct print statements with event emission for better integration
        with plugins and UI systems.

        Args:
            message: The message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR)

        Example:
            >>> agent.log("Processing request", level="INFO")
            >>> agent.log("Something went wrong!", level="ERROR")
        """
        # Map log level to EventType and logger level
        event_map = {
            "DEBUG": EventType.LOG_DEBUG,
            "INFO": EventType.LOG_INFO,
            "WARNING": EventType.LOG_WARNING,
            "ERROR": EventType.LOG_ERROR,
        }
        logger_method_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
        }

        event_type = event_map.get(level, EventType.LOG_INFO)
        logger_method = logger_method_map.get(level, self.logger.info)

        # Log to Python logger
        logger_method(f"{self.name}: {message}")

        # Emit structured event if orchestrator has event bus
        if hasattr(self.orchestrator, "emit_event"):
            self.emit_event(
                event_type,
                {"message": message, "timestamp": datetime.utcnow().isoformat()},
            )

    def emit_event(self, event_type: EventType, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Emit a structured event through the orchestrator.

        Allows agents to emit domain-specific events (e.g., AGENT_START, CONFLICT_DETECTED).

        Args:
            event_type: The type of event to emit
            data: Optional data to include with the event

        Example:
            >>> self.emit_event(EventType.AGENT_START, {"action": "process"})
        """
        if data is None:
            data = {}

        # Add agent context if not already present
        if "agent" not in data:
            data["agent"] = self.name

        # Emit through orchestrator
        if hasattr(self.orchestrator, "emit_event"):
            self.orchestrator.emit_event(event_type, data)
        else:
            self.logger.debug(f"Event emitted (no orchestrator support): {event_type}")

    def suggest_knowledge_addition(
        self,
        content: str,
        category: str,
        topic: Optional[str] = None,
        difficulty: str = "intermediate",
        reason: str = "insufficient_context",
    ) -> None:
        """
        Suggest adding knowledge when agent detects a gap.

        This enables automatic knowledge enrichment when agents encounter
        topics or patterns that should be remembered for the project.

        Args:
            content: The knowledge content to remember
            category: Knowledge category (e.g., 'technical', 'domain_specific')
            topic: Specific topic within category
            difficulty: beginner, intermediate, or advanced
            reason: Why this knowledge is being suggested

        Example:
            >>> self.suggest_knowledge_addition(
            ...     content="REST APIs use HTTP methods for CRUD operations",
            ...     category="api_design",
            ...     topic="rest_conventions",
            ...     difficulty="intermediate",
            ...     reason="insufficient_context"
            ... )
        """
        self.emit_event(
            EventType.KNOWLEDGE_SUGGESTION,
            {
                "content": content,
                "category": category,
                "topic": topic or category,
                "difficulty": difficulty,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
