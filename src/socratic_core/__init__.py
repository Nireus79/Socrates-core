"""
Socratic Core - Foundation services for modular Socrates AI platform.

Core components:
- BaseService: Abstract base for all services
- ServiceOrchestrator: Central orchestrator managing all services
- EventBus: Event-driven communication system
- Shared Models: Common data structures used across services
"""

from socratic_core.base_service import BaseService
from socratic_core.config import ConfigBuilder, SocratesConfig
from socratic_core.event_bus import Event, EventBus
from socratic_core.events import EventEmitter, EventType
from socratic_core.exceptions import (
    AgentError,
    APIError,
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    ProjectNotFoundError,
    SocratesError,
    UserNotFoundError,
    ValidationError,
)
from socratic_core.orchestrator import ServiceOrchestrator
from socratic_core.shared_models import (
    IdentifiedModel,
    Interaction,
    InteractionStatus,
    Metric,
    Recommendation,
    Skill,
    SkillType,
    TimestampedModel,
    WorkflowStatus,
)
from socratic_core.utils import (
    ProjectIDGenerator,
    TTLCache,
    UserIDGenerator,
    cached,
    deserialize_datetime,
    serialize_datetime,
)

__version__ = "0.1.0"

__all__ = [
    # Configuration
    "SocratesConfig",
    "ConfigBuilder",
    # Service layer
    "BaseService",
    "ServiceOrchestrator",
    # Event system
    "Event",
    "EventBus",
    "EventEmitter",
    "EventType",
    # Exceptions
    "SocratesError",
    "ConfigurationError",
    "DatabaseError",
    "ValidationError",
    "AuthenticationError",
    "APIError",
    "AgentError",
    "ProjectNotFoundError",
    "UserNotFoundError",
    # Models - Enums
    "InteractionStatus",
    "SkillType",
    "WorkflowStatus",
    # Models - Classes
    "Interaction",
    "Skill",
    "Metric",
    "Recommendation",
    "TimestampedModel",
    "IdentifiedModel",
    # Utilities
    "serialize_datetime",
    "deserialize_datetime",
    "ProjectIDGenerator",
    "UserIDGenerator",
    "TTLCache",
    "cached",
]
