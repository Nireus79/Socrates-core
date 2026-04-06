# Socratic Core

Foundation services library for the modular Socrates AI platform. Provides core infrastructure, database abstraction, service orchestration, event-driven communication, and service mesh management.

## Features

### Core Capabilities
- **BaseService Framework**: Abstract base class for all Socratic services with lifecycle management
- **Service Orchestrator**: Central orchestration managing multi-service workflows and dependencies
- **Event Bus**: Pub/sub event-driven communication system with async/await support
- **Database Abstraction**: Unified interface for SQLite and PostgreSQL
- **Service Mesh**: Distributed service management with health checks, load balancing, and resilience patterns
- **Circuit Breaker Pattern**: Automatic failure detection and cascading failure prevention
- **Configuration Management**: Centralized configuration using builder pattern
- **Shared Models**: Common data structures (User, Project, Session, Interaction, Question, Skill, Metric, Recommendation)
- **Utility Functions**: Serialization, ID generation, TTL caching

## Installation

```bash
pip install socratic-core
```

## Quick Start

### 1. Configure the Platform

```python
from socratic_core import ConfigBuilder

config = ConfigBuilder() \
    .set_database_path("socrates.db") \
    .set_log_level("INFO") \
    .set_environment("development") \
    .build()
```

### 2. Initialize Database

```python
from socratic_core import SQLiteClient

db = SQLiteClient("socrates.db")
await db.connect()
await db.initialize_schema()

# Create a user
await db.save_entity("user", "u123", {
    "username": "john_doe",
    "email": "john@example.com",
    "subscription_tier": "pro"
})

# Query users
users = await db.query_entities("user", filters={"subscription_tier": "pro"})
```

### 3. Create a Custom Service

```python
from socratic_core import BaseService

class AnalysisService(BaseService):
    async def initialize(self):
        await super().initialize()
        self.logger.info("Analysis service initialized")

    async def execute(self, action: str, params: dict):
        if action == "analyze_project":
            return await self.analyze_project(params)
        elif action == "get_metrics":
            return await self.get_metrics(params)
        return None

    async def analyze_project(self, params: dict):
        project_id = params.get("project_id")
        # Implementation here
        return {"analysis": "complete", "insights": []}

    async def get_metrics(self, params: dict):
        user_id = params.get("user_id")
        # Implementation here
        return {"metrics": {}}
```

### 4. Use Event Bus

```python
from socratic_core import EventBus, Event

bus = EventBus()

# Subscribe to events
@bus.on("project:created")
async def on_project_created(event: Event):
    print(f"Project created: {event.data['name']}")

@bus.on("interaction:completed")
async def on_interaction_completed(event: Event):
    print(f"Interaction done: {event.data}")

# Emit events from your services
event = Event(
    event_type="project:created",
    data={
        "project_id": "p123",
        "name": "My Project",
        "user_id": "u456"
    }
)
await bus.emit(event)
```

### 5. Set Up Service Mesh

```python
from socratic_core import ServiceMesh, LoadBalancer, ServiceMeshProxy

# Create mesh
mesh = ServiceMesh("socratic_mesh")
lb = LoadBalancer(mesh)
proxy = ServiceMeshProxy(mesh, lb)

# Register services
agents_svc = mesh.register_service(
    "socratic-agents",
    "1.0.0",
    "localhost",
    8001,
    tags=["nlp", "generation"]
)

rag_svc = mesh.register_service(
    "socratic-rag",
    "1.0.0",
    "localhost",
    8002,
    tags=["retrieval", "search"]
)

# Register instances
mesh.register_instance("socratic-agents", "agent-1")
mesh.register_instance("socratic-agents", "agent-2")

# Use through proxy with load balancing
instance = lb.select_instance("socratic-agents", strategy="round_robin")
```

## API Reference

### Database Operations

```python
# Save/update entity
await db.save_entity("project", "p123", {
    "user_id": "u456",
    "name": "Q1 Analysis",
    "phase": "discovery"
})

# Load entity
user = await db.load_entity("user", "u123")

# Query with filters
sessions = await db.query_entities(
    "session",
    filters={"user_id": "u123"},
    limit=10,
    offset=0
)

# Delete entity
await db.delete_entity("project", "p123")

# Raw query
results = await db.execute_query(
    "SELECT * FROM users WHERE subscription_tier = ?",
    {"subscription_tier": "pro"}
)
```

### Event Bus

```python
# Register event handler (decorator style)
@bus.on("event:type")
async def handler(event: Event):
    pass

# Register multiple handlers
bus.subscribe("event:type", handler1)
bus.subscribe("event:type", handler2)

# Emit event
event = Event(event_type="event:type", data={...})
await bus.emit(event)

# Get event statistics
stats = bus.get_stats()
```

### Service Mesh

```python
# Get mesh status
status = mesh.get_mesh_status()
# Returns: {
#   "total_services": 5,
#   "total_instances": 10,
#   "healthy_instances": 9,
#   "health_percentage": 90.0
# }

# Check health
health = mesh.check_health("socratic-agents", "agent-1")

# Get healthy instances
healthy = mesh.get_healthy_instances("socratic-agents")

# Load balancing strategies
instance = lb.select_instance("socratic-agents", "round_robin")
instance = lb.select_instance("socratic-agents", "least_connections")
instance = lb.select_instance("socratic-agents", "weighted")
instance = lb.select_instance("socratic-agents", "random")
```

## Core Components

### BaseService

All Socratic services inherit from BaseService:

```python
class BaseService:
    - initialize(): async setup
    - execute(action, params): async execution
    - shutdown(): async cleanup
    - health_check(): status check
    - get_status(): current status
```

### Shared Models

Common data structures used across services:

- **User**: User profiles with subscription tiers
- **Project**: User projects with phase tracking
- **Session**: User interaction sessions
- **Interaction**: Agent-user interactions with metrics
- **Question**: Project questions across discovery/design/build/test phases
- **Skill**: User skills with proficiency levels
- **Metric**: Performance metrics and KPIs
- **Recommendation**: AI-generated recommendations

### Database Schema

Core tables for all entities:
- users: User profiles and metadata
- projects: Project definitions and phase tracking
- sessions: Session tracking and duration
- interactions: Agent interactions with input/output/metrics
- questions: Phase-specific questions
- patterns: Detected behavior patterns
- metrics: Performance and usage metrics
- recommendations: AI recommendations

### Service Mesh Features

- **Health Checking**: Automatic health status monitoring
- **Load Balancing**: Multiple strategies for instance selection
- **Circuit Breaker**: Prevents cascading failures
- **Metrics**: Request count, error rate, response time tracking
- **Service Discovery**: Dynamic service registration
- **Request Interception**: Middleware pattern for cross-cutting concerns

## Configuration

```python
from socratic_core import ConfigBuilder

config = ConfigBuilder() \
    .set_database_path("socrates.db") \
    .set_database_type("sqlite")  # or "postgresql" \
    .set_log_level("DEBUG")  # DEBUG, INFO, WARNING, ERROR \
    .set_environment("development")  # or production, staging \
    .set_max_workers(10) \
    .set_request_timeout(30) \
    .set_cache_enabled(True) \
    .set_cache_ttl(3600) \
    .build()
```

## Error Handling

```python
from socratic_core import (
    SocratesError,
    DatabaseError,
    ConfigurationError,
    ValidationError,
    AuthenticationError,
    ProjectNotFoundError,
    UserNotFoundError,
)

try:
    user = await db.load_entity("user", "invalid_id")
except DatabaseError:
    print("Database connection failed")
except UserNotFoundError:
    print("User does not exist")
except SocratesError as e:
    print(f"Generic error: {e}")
```

## Examples

See `examples/` directory for:
- Basic service setup
- Database operations
- Event-driven workflows
- Service mesh configuration
- Multi-service orchestration

## Performance Tuning

1. **Database**: Use SQLite for development, PostgreSQL for production
2. **Caching**: Use `@cached` decorator for expensive operations
3. **Batching**: Query multiple entities with filters instead of individual loads
4. **Connection Pooling**: PostgreSQL client supports connection pooling
5. **Load Balancing**: Use weighted strategy for heterogeneous instances

## Testing

```python
import pytest

@pytest.fixture
async def db():
    db = SQLiteClient(":memory:")
    await db.connect()
    await db.initialize_schema()
    yield db
    await db.disconnect()

@pytest.mark.asyncio
async def test_user_operations(db):
    await db.save_entity("user", "u123", {"username": "test"})
    user = await db.load_entity("user", "u123")
    assert user["username"] == "test"
```

## Architecture

```
┌─────────────────────────────────────────┐
│        Application Services             │
│  (Agents, RAG, Conflict, Learning, etc) │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Orchestration & Communication       │
│  ServiceOrchestrator, EventBus, Mesh    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Core Infrastructure Services         │
│  Database, Config, Utils, Models        │
└─────────────────────────────────────────┘
```

## Contributing

See CONTRIBUTING.md for development guidelines.

## License

MIT
