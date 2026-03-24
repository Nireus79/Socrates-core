"""
Event system for Socratic Core.

Provides event emission and handling capabilities.
"""

from enum import Enum
from typing import Any, Callable, Dict, List


class EventType(str, Enum):
    """Types of events in the system."""

    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_INITIALIZED = "system_initialized"
    SYSTEM_STOPPED = "system_stopped"
    SYSTEM_ERROR = "system_error"

    # Service events
    SERVICE_INITIALIZED = "service_initialized"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_ERROR = "service_error"

    # Agent events
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_SKILL_UPDATED = "agent_skill_updated"

    # Learning events
    LEARNING_STARTED = "learning_started"
    LEARNING_COMPLETED = "learning_completed"
    MATURITY_UPDATED = "maturity_updated"
    SKILL_GENERATED = "skill_generated"

    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"

    # Data events
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"


class EventEmitter:
    """Simple event emitter for decoupled communication."""

    def __init__(self):
        """Initialize event emitter."""
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, listener: Callable) -> None:
        """
        Register a listener for an event.

        Args:
            event: Event name
            listener: Callable to invoke when event occurs
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)

    def off(self, event: str, listener: Callable) -> None:
        """
        Unregister a listener for an event.

        Args:
            event: Event name
            listener: Callable to remove
        """
        if event in self._listeners:
            self._listeners[event].remove(listener)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        Emit an event to all registered listeners.

        Args:
            event: Event name
            *args: Positional arguments for listeners
            **kwargs: Keyword arguments for listeners
        """
        if event in self._listeners:
            for listener in self._listeners[event]:
                try:
                    listener(*args, **kwargs)
                except Exception as e:
                    # Log error but don't fail
                    print(f"Error in event listener for {event}: {e}")

    def once(self, event: str, listener: Callable) -> None:
        """
        Register a one-time listener for an event.

        Args:
            event: Event name
            listener: Callable to invoke once when event occurs
        """

        def one_time_listener(*args: Any, **kwargs: Any) -> None:
            listener(*args, **kwargs)
            self.off(event, one_time_listener)

        self.on(event, one_time_listener)
