# Socratic Core - API Reference

## Configuration API

### ConfigBuilder

Builder for constructing configuration objects.

```python
from socratic_core import ConfigBuilder, SocratesConfig

builder = ConfigBuilder()

# Database configuration
builder.set_database_path("path/to/socrates.db")
builder.set_database_type("sqlite")  # or "postgresql"
builder.set_connection_pool_size(10)  # For PostgreSQL

# Environment configuration
builder.set_environment("development")  # development|staging|production
builder.set_log_level("INFO")  # DEBUG|INFO|WARNING|ERROR
builder.set_debug_mode(True)

# Service configuration
builder.set_max_workers(10)
builder.set_request_timeout(30)  # seconds
builder.set_service_mesh_enabled(True)

# Cache configuration
builder.set_cache_enabled(True)
builder.set_cache_ttl(3600)  # seconds
builder.set_cache_max_size(1000)

# Build configuration
config: SocratesConfig = builder.build()
```

## Database API

### DatabaseClient (Abstract Interface)

```python
from socratic_core import DatabaseClient, SQLiteClient

class DatabaseClient(ABC):
    @abstractmethod
    async def connect() -> None: ...

    @abstractmethod
    async def disconnect() -> None: ...

    @abstractmethod
    async def initialize_schema() -> None: ...

    @abstractmethod
    async def save_entity(entity_type: str, entity_id: str, data: Dict) -> bool: ...

    @abstractmethod
    async def load_entity(entity_type: str, entity_id: str) -> Optional[Dict]: ...

    @abstractmethod
    async def delete_entity(entity_type: str, entity_id: str) -> bool: ...

    @abstractmethod
    async def query_entities(
        entity_type: str,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict]: ...

    @abstractmethod
    async def execute_query(query: str, params: Optional[Dict] = None) -> Any: ...

    @abstractmethod
    async def transaction() -> Any: ...
```

### SQLiteClient

SQLite implementation of DatabaseClient.

```python
from socratic_core import SQLiteClient

# Create client
db = SQLiteClient("path/to/database.db")
# or in-memory
db = SQLiteClient(":memory:")

# Connect and initialize
await db.connect()
await db.initialize_schema()

# Save entity
success = await db.save_entity("user", "u123", {
    "username": "john_doe",
    "email": "john@example.com",
    "subscription_tier": "pro"
})

# Load entity
user = await db.load_entity("user", "u123")
# Returns: {
#     "user_id": "u123",
#     "username": "john_doe",
#     "email": "john@example.com",
#     "subscription_tier": "pro",
#     "created_at": "2024-04-06T12:00:00",
#     "updated_at": "2024-04-06T12:00:00",
#     "metadata": {}
# }

# Query entities with filters
users = await db.query_entities(
    "user",
    filters={"subscription_tier": "pro"},
    limit=10,
    offset=0
)

# Delete entity
deleted = await db.delete_entity("user", "u123")

# Raw SQL query
results = await db.execute_query(
    "SELECT * FROM users WHERE email LIKE ?",
    {"email": "%@example.com"}
)

# Disconnect
await db.disconnect()
```

### PostgresClient

PostgreSQL implementation (stub for future use).

```python
from socratic_core import PostgresClient

db = PostgresClient("postgresql://user:password@localhost/socrates")
# All methods currently raise NotImplementedError
```

## Event Bus API

### Event

Immutable event object.

```python
from socratic_core import Event

event = Event(
    event_type="project:created",
    data={
        "project_id": "p123",
        "name": "My Project",
        "created_by": "u456"
    },
    source="socratic-agents"
)

# Access event properties
event.event_type  # str
event.data  # dict
event.source  # str
event.timestamp  # float (Unix timestamp)
event.event_id  # str (unique ID)
```

### EventBus

Central pub/sub event manager.

```python
from socratic_core import EventBus, Event

bus = EventBus()

# Register handler using decorator
@bus.on("project:created")
async def on_project_created(event: Event):
    project_id = event.data.get("project_id")
    print(f"Project created: {project_id}")

# Register handler using method
async def on_interaction_completed(event: Event):
    print(f"Interaction done: {event.data}")

bus.subscribe("interaction:completed", on_interaction_completed)

# Emit event
event = Event(
    event_type="project:created",
    data={"project_id": "p123", "name": "Q1 Analysis"}
)
await bus.emit(event)

# Unsubscribe
bus.unsubscribe("project:created", on_project_created)

# Get bus statistics
stats = bus.get_stats()
# Returns: {
#     "total_events": 150,
#     "event_types": ["project:created", "interaction:completed"],
#     "subscriber_count": 8
# }
```

### Built-in Events

```python
# System events
Event("system:startup", {})
Event("system:shutdown", {})

# Project events
Event("project:created", {"project_id": "p123", "name": "...", "user_id": "u456"})
Event("project:updated", {"project_id": "p123", "phase": "design"})
Event("project:deleted", {"project_id": "p123"})

# Interaction events
Event("interaction:started", {"interaction_id": "i123", "agent": "..."})
Event("interaction:completed", {"interaction_id": "i123", "result": "..."})
Event("interaction:failed", {"interaction_id": "i123", "error": "..."})

# Question events
Event("question:answered", {"question_id": "q123", "answer": "..."})
Event("question:pending", {"question_id": "q123", "phase": "discovery"})

# User events
Event("user:registered", {"user_id": "u123", "username": "..."})
Event("user:deleted", {"user_id": "u123"})
```

## Service Mesh API

### ServiceMesh

Manages services and instances in distributed system.

```python
from socratic_core import ServiceMesh

mesh = ServiceMesh("socratic_mesh")

# Register service
service_meta = mesh.register_service(
    name="socratic-agents",
    version="1.0.0",
    host="localhost",
    port=8001,
    protocol="http",  # http|grpc|tcp
    tags=["nlp", "generation"]
)

# Register service instance
instance = mesh.register_instance(
    service_name="socratic-agents",
    instance_id="agent-1"
)

# Check instance health
health = mesh.check_health("socratic-agents", "agent-1")
# Returns: HealthStatus.HEALTHY | .UNHEALTHY | .DEGRADED | .UNKNOWN

# Get healthy instances
healthy = mesh.get_healthy_instances("socratic-agents")

# Get available instances (healthy + degraded)
available = mesh.get_available_instances("socratic-agents")

# Record request metrics
mesh.record_request(
    service_name="socratic-agents",
    instance_id="agent-1",
    response_time_ms=125.5,
    is_error=False
)

# Get mesh status
status = mesh.get_mesh_status()
# Returns: {
#     "mesh_name": "socratic_mesh",
#     "total_services": 5,
#     "total_instances": 12,
#     "healthy_instances": 11,
#     "health_percentage": 91.67,
#     "services": {
#         "socratic-agents": {"version": "1.0.0", "instances": 3, "healthy": 3},
#         ...
#     }
# }
```

### LoadBalancer

Selects service instances using various strategies.

```python
from socratic_core import LoadBalancer, ServiceMesh

mesh = ServiceMesh()
lb = LoadBalancer(mesh)

# Round-robin: distributes evenly across instances
instance = lb.select_instance("socratic-agents", "round_robin")

# Least connections: picks instance with fewest requests
instance = lb.select_instance("socratic-agents", "least_connections")

# Weighted: considers instance weight and error rate
instance = lb.select_instance("socratic-agents", "weighted")

# Random: random selection
instance = lb.select_instance("socratic-agents", "random")

# Returns: ServiceInstance | None
if instance:
    url = f"{instance.service.protocol}://{instance.service.host}:{instance.service.port}"
```

### ServiceMeshProxy

Makes calls to services through the mesh.

```python
from socratic_core import ServiceMeshProxy, ServiceMesh, LoadBalancer

mesh = ServiceMesh()
lb = LoadBalancer(mesh)
proxy = ServiceMeshProxy(mesh, lb)

# Register interceptor (middleware)
async def auth_interceptor(instance, endpoint, kwargs):
    kwargs["headers"] = kwargs.get("headers", {})
    kwargs["headers"]["Authorization"] = "Bearer token"

proxy.register_interceptor("socratic-agents", auth_interceptor)

# Call service through mesh
try:
    response = await proxy.call_service(
        service_name="socratic-agents",
        endpoint="/analyze",
        method="POST",
        data={"text": "..."}
    )
except RuntimeError as e:
    if "Circuit breaker" in str(e):
        print("Service temporarily unavailable")
    else:
        print("No available instances")
```

### Health Status

```python
from socratic_core import HealthStatus

# Possible health statuses
HealthStatus.HEALTHY  # Service is functioning normally
HealthStatus.UNHEALTHY  # Service is down or erroring severely
HealthStatus.DEGRADED  # Service is responding but with errors
HealthStatus.UNKNOWN  # Health status not yet determined
```

## Service Orchestrator API

### ServiceOrchestrator

Centrally coordinates multiple services.

```python
from socratic_core import ServiceOrchestrator, BaseService

orchestrator = ServiceOrchestrator()

# Register service
class MyService(BaseService):
    async def execute(self, action: str, params: dict):
        if action == "process":
            return {"result": "processed"}

service = MyService("my-service", {})
orchestrator.register_service("my-service", service)

# Start service
await orchestrator.start_service("my-service")

# Get service status
status = orchestrator.get_service_status("my-service")  # str: "running", "stopped", "error"

# Execute service action
result = await orchestrator.execute_service(
    "my-service",
    action="process",
    params={"data": "value"}
)

# Shutdown all services
await orchestrator.shutdown()
```

## BaseService API

### BaseService

Base class for all Socratic services.

```python
from socratic_core import BaseService

class CustomService(BaseService):
    """Custom service implementation."""

    def __init__(self, service_name: str, config: dict):
        super().__init__(service_name, config)

    async def initialize(self):
        """Initialize service. Called when service starts."""
        await super().initialize()
        self.logger.info(f"Initializing {self.service_name}")
        # Custom initialization

    async def execute(self, action: str, params: dict) -> Any:
        """Execute an action. Main entry point for service operations."""
        if action == "analyze":
            return await self.analyze(params)
        elif action == "get_status":
            return await self.get_status()
        return None

    async def analyze(self, params: dict):
        """Example action implementation."""
        result = {}
        try:
            # Business logic
            result["success"] = True
        except Exception as e:
            self.logger.error(f"Error: {e}")
            result["error"] = str(e)
        return result

    async def shutdown(self):
        """Cleanup when service stops."""
        await super().shutdown()
        self.logger.info(f"Shutting down {self.service_name}")
        # Custom cleanup

    async def health_check(self) -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": self.service_name,
            "uptime_seconds": time.time() - self.start_time
        }

# Use service
service = CustomService("custom-service", {"debug": True})
await service.initialize()
result = await service.execute("analyze", {"data": "..."})
await service.shutdown()
```

## Shared Models API

### User Model

```python
from socratic_core import User

user = User(
    user_id="u123",
    username="john_doe",
    email="john@example.com",
    subscription_tier="pro",
    subscription_date="2024-01-01",
    metadata={"preferences": {"theme": "dark"}}
)
```

### Project Model

```python
from socratic_core import Project

project = Project(
    project_id="p123",
    user_id="u123",
    name="Q1 Analysis",
    phase="discovery",  # discovery|design|build|test
    description="Quarterly analysis project",
    metadata={"tags": ["analysis", "2024"]}
)
```

### Session Model

```python
from socratic_core import Session

session = Session(
    session_id="s123",
    user_id="u123",
    project_id="p123",
    started_at="2024-04-06T10:00:00",
    ended_at="2024-04-06T11:00:00",
    metadata={"device": "web"}
)
```

### Interaction Model

```python
from socratic_core import Interaction, InteractionStatus

interaction = Interaction(
    interaction_id="i123",
    session_id="s123",
    user_id="u123",
    agent_name="socratic-agents",
    agent_type="question_generator",
    input_data={"topic": "machine_learning"},
    output_data={"questions": [...]},
    status=InteractionStatus.COMPLETED,
    timestamp="2024-04-06T10:05:00",
    duration_ms=450.5,
    error_message=None,
    metadata={"model": "claude-3"}
)
```

### Question Model

```python
from socratic_core import Question

question = Question(
    question_id="q123",
    project_id="p123",
    phase="discovery",
    question="What is the problem you're trying to solve?",
    status="answered",
    answer="We need to optimize database queries",
    created_at="2024-04-06T10:00:00",
    answered_at="2024-04-06T10:30:00"
)
```

### Skill Model

```python
from socratic_core import Skill, SkillType

skill = Skill(
    skill_id="sk123",
    user_id="u123",
    name="Python",
    skill_type=SkillType.TECHNICAL,
    proficiency_level=4,  # 1-5
    endorsed_by=15,
    created_at="2024-01-01"
)
```

### Metric Model

```python
from socratic_core import Metric

metric = Metric(
    metric_id="m123",
    session_id="s123",
    user_id="u123",
    metric_type="response_time",
    metric_value=125.5,
    recorded_at="2024-04-06T10:05:00"
)
```

### Recommendation Model

```python
from socratic_core import Recommendation

rec = Recommendation(
    recommendation_id="r123",
    user_id="u123",
    recommendation_type="learning_path",
    content="Consider learning Advanced Database Design",
    confidence=0.85,
    created_at="2024-04-06T10:00:00"
)
```

## Utility Functions API

### ID Generators

```python
from socratic_core import UserIDGenerator, ProjectIDGenerator

# Generate IDs
user_id = UserIDGenerator.generate()  # "u_xxxxxx"
project_id = ProjectIDGenerator.generate()  # "p_xxxxxx"
```

### Datetime Serialization

```python
from socratic_core import serialize_datetime, deserialize_datetime
from datetime import datetime

dt = datetime.now()
serialized = serialize_datetime(dt)  # ISO format string
deserialized = deserialize_datetime(serialized)  # datetime object
```

### Caching Decorator

```python
from socratic_core import cached

@cached(ttl=3600)  # 1 hour
async def expensive_operation(param1: str):
    # This will be cached for 1 hour
    return {"result": "..."}

# Call function
result = await expensive_operation("value")
```

### TTL Cache

```python
from socratic_core import TTLCache

cache = TTLCache(ttl=3600)  # 1 hour TTL

# Set value
cache.set("key", "value")

# Get value
value = cache.get("key")  # returns value if not expired, None otherwise

# Clear cache
cache.clear()
```

## Exception Hierarchy

```python
from socratic_core import (
    SocratesError,  # Base exception
    DatabaseError,
    ConfigurationError,
    ValidationError,
    AuthenticationError,
    APIError,
    AgentError,
    ProjectNotFoundError,
    UserNotFoundError,
)

try:
    user = await db.load_entity("user", "u123")
except UserNotFoundError:
    print("User does not exist")
except DatabaseError as e:
    print(f"Database error: {e}")
except SocratesError as e:
    print(f"General Socratic error: {e}")
```

## Best Practices

1. **Always use async/await**: All I/O operations are async
2. **Manage database connections**: Use `connect()` and `disconnect()`
3. **Subscribe to relevant events**: Use event bus for async communication
4. **Check instance health**: Verify service health before calls
5. **Use load balancing**: Always select instances through LoadBalancer
6. **Handle exceptions**: Catch specific exception types
7. **Log important events**: Use service logger for debugging
