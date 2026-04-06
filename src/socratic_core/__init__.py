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
from socratic_core.database import DatabaseClient, PostgresClient, SQLiteClient
from socratic_core.connection_pool import ConnectionPool, SQLiteConnectionPool, PostgresConnectionPool
from socratic_core.migrations import MigrationRunner, Migration, get_default_migrations, MigrationError
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
from socratic_core.service_mesh import (
    HealthStatus,
    LoadBalancer,
    ServiceInstance,
    ServiceMesh,
    ServiceMeshProxy,
    ServiceMetadata,
)
from socratic_core.shared_models import (
    IdentifiedModel,
    Interaction,
    InteractionStatus,
    Metric,
    Project,
    Question,
    Recommendation,
    Session,
    Skill,
    SkillType,
    TimestampedModel,
    User,
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

__version__ = "0.2.0"

__all__ = [
    # Configuration
    "SocratesConfig",
    "ConfigBuilder",
    # Service layer
    "BaseService",
    "ServiceOrchestrator",
    # Service Mesh
    "ServiceMesh",
    "ServiceMeshProxy",
    "LoadBalancer",
    "ServiceInstance",
    "ServiceMetadata",
    "HealthStatus",
    # Database
    "DatabaseClient",
    "SQLiteClient",
    "PostgresClient",
    "ConnectionPool",
    "SQLiteConnectionPool",
    "PostgresConnectionPool",
    # Migrations
    "MigrationRunner",
    "Migration",
    "MigrationError",
    "get_default_migrations",
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
    "User",
    "Project",
    "Session",
    "Question",
    # Utilities
    "serialize_datetime",
    "deserialize_datetime",
    "ProjectIDGenerator",
    "UserIDGenerator",
    "TTLCache",
    "cached",
]
