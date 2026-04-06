# Socratic Core - Architecture

## System Architecture

Socratic Core provides the foundational infrastructure for the modular Socrates platform. It's organized in layers from configuration and database to service orchestration and inter-service communication.

```
┌──────────────────────────────────────────────────────────────┐
│                   Application Services                        │
│  (socratic-agents, socratic-rag, socratic-conflict, etc.)    │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│              Orchestration & Communication Layer              │
├──────────────────────────────────────────────────────────────┤
│  ServiceOrchestrator  │  EventBus  │  ServiceMesh  │  Proxy  │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│             Core Infrastructure Services Layer               │
├──────────────────────────────────────────────────────────────┤
│  DatabaseClient  │  Config  │  Shared Models  │  Utils       │
└──────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Configuration Layer

**Purpose**: Centralized configuration management using builder pattern.

**Key Classes**:
- `ConfigBuilder`: Builder for constructing `SocratesConfig`
- `SocratesConfig`: Immutable configuration object

**Responsibilities**:
- Database path and type selection
- Environment (development/production/staging)
- Logging configuration
- Service mesh settings
- Cache settings
- Worker threads and timeouts

**Key Methods**:
```python
ConfigBuilder()
  .set_database_path(path)
  .set_database_type(type)
  .set_log_level(level)
  .set_environment(env)
  .set_max_workers(count)
  .set_request_timeout(seconds)
  .build()
```

### 2. Database Layer

**Purpose**: Abstract persistent data storage with unified interface.

**Architecture**:

```
┌─────────────────────────────────┐
│   DatabaseClient (Interface)    │
└─────────────────────────────────┘
         ▲              ▲
         │              │
    ┌────┴──┐      ┌────┴──────────┐
    │        │      │               │
SQLiteClient │  PostgresClient  Mongo*
```

**Key Classes**:
- `DatabaseClient`: Abstract interface defining CRUD operations
- `SQLiteClient`: SQLite implementation (production-ready)
- `PostgresClient`: PostgreSQL stub (planned)

**CRUD Operations**:
```python
await db.save_entity(entity_type, entity_id, data)
await db.load_entity(entity_type, entity_id)
await db.delete_entity(entity_type, entity_id)
await db.query_entities(entity_type, filters, limit, offset)
await db.execute_query(raw_sql, params)
await db.transaction()
```

**Supported Entity Types**:
- `user`: User profiles
- `project`: Projects/workspaces
- `session`: User sessions
- `interaction`: Agent-user interactions
- `question`: Phase-specific questions
- `pattern`: Detected patterns
- `metric`: Performance metrics
- `recommendation`: AI recommendations

### 3. Shared Models Layer

**Purpose**: Common data structures ensuring consistency across services.

**Key Models**:

```python
# Enums
InteractionStatus: in_progress, completed, failed, cancelled
SkillType: technical, soft, cognitive, domain
WorkflowStatus: pending, running, completed, failed

# Base Models
TimestampedModel: Base with created_at, updated_at
IdentifiedModel: Base with unique ID

# Domain Models
User(IdentifiedModel):
  - user_id, username, email
  - subscription_tier, subscription_date
  - metadata, preferences

Project(IdentifiedModel):
  - project_id, user_id, name
  - phase (discovery, design, build, test)
  - description, created_at, updated_at

Session(IdentifiedModel):
  - session_id, user_id, project_id
  - started_at, ended_at, duration_ms
  - metadata, status

Interaction(IdentifiedModel):
  - interaction_id, session_id, user_id
  - agent_name, agent_type
  - input_data, output_data
  - status, timestamp, duration_ms
  - error_message, metadata

Question(IdentifiedModel):
  - question_id, project_id, phase
  - question, answer, status
  - created_at, answered_at

Skill(IdentifiedModel):
  - skill_id, user_id, name
  - skill_type, proficiency_level
  - endorsed_by (count), created_at

Metric(IdentifiedModel):
  - metric_id, metric_type
  - metric_value, recorded_at
  - session_id, user_id

Recommendation(IdentifiedModel):
  - recommendation_id, user_id
  - recommendation_type, content
  - confidence, created_at
```

### 4. Event Bus (Pub/Sub)

**Purpose**: Event-driven communication between services.

**Architecture**:

```
Service A ──┐
            │
            ├─→ Event Bus ──→ Handler 1
            │                 Handler 2
Service B ──┤                 Handler 3
            │
            └─→ Event Bus ──→ Custom Logic
```

**Key Classes**:
- `Event`: Immutable event with type, data, source, timestamp
- `EventBus`: Central pub/sub manager
- `EventEmitter`: Helper for emitting events

**Patterns**:

1. **Decorator-based Registration**:
```python
@bus.on("project:created")
async def on_project_created(event: Event):
    pass
```

2. **Subscription**:
```python
bus.subscribe("project:created", handler_func)
```

3. **Event Emission**:
```python
event = Event(
    event_type="project:created",
    data={"project_id": "p123", "name": "..."},
    source="socratic-agents"
)
await bus.emit(event)
```

**Built-in Events**:
- `system:startup`: System initialization
- `system:shutdown`: System shutdown
- `project:created`, `project:updated`, `project:deleted`
- `interaction:started`, `interaction:completed`, `interaction:failed`
- `question:answered`, `question:pending`
- `user:registered`, `user:deleted`

### 5. Service Mesh Layer

**Purpose**: Distributed service management with load balancing, health checks, and resilience patterns.

**Architecture**:

```
┌──────────────────────────────────────────┐
│         ServiceMesh                      │
├──────────────────────────────────────────┤
│ Services Registry    │  Instances List   │
│ Circuit Breakers     │  Health Status    │
└──────────────────────────────────────────┘
           ▲              ▲
           │              │
       ┌───┴──────┬───────┴─────┐
       │          │              │
    LoadBalancer  Health Check  Metrics
```

**Key Classes**:

1. **ServiceMesh**:
   - Register services and instances
   - Health checking
   - Circuit breaker management
   - Mesh status reporting

2. **ServiceInstance**:
   - Instance metadata
   - Health status
   - Response time tracking
   - Error rate calculation

3. **LoadBalancer**:
   - Multiple balancing strategies
   - Instance selection

4. **ServiceMeshProxy**:
   - Request interception
   - Middleware support
   - Circuit breaker enforcement

**Load Balancing Strategies**:

1. **Round Robin**: Distributes evenly across instances
   ```python
   instance = lb.select_instance("service", "round_robin")
   ```

2. **Least Connections**: Picks instance with fewest requests
   ```python
   instance = lb.select_instance("service", "least_connections")
   ```

3. **Random**: Random selection
   ```python
   instance = lb.select_instance("service", "random")
   ```

4. **Weighted**: Weight-aware selection
   ```python
   instance = lb.select_instance("service", "weighted")
   ```

**Circuit Breaker Pattern**:

```
        Request
          │
    ┌─────▼──────┐
    │   Closed   │  ◄──── Requests pass through
    │   (Normal) │  ◄──── Failures counted
    └─────┬──────┘
          │ (5+ failures)
    ┌─────▼──────┐
    │    Open    │  ◄──── Requests rejected
    │ (Failed)   │  ◄──── Wait for timeout
    └─────┬──────┘
          │ (60s timeout)
    ┌─────▼──────┐
    │ Half-Open  │  ◄──── Test requests
    │  (Testing) │  ◄──── 2+ successes → Closed
    └────────────┘
```

### 6. Service Orchestrator

**Purpose**: Central coordination of multi-service workflows.

**Key Responsibilities**:
- Service lifecycle management
- Dependency resolution
- Workflow execution
- Error handling and recovery
- Graceful shutdown coordination

**Key Methods**:
```python
orchestrator.register_service(name, service_instance)
orchestrator.start_service(name)
orchestrator.execute_workflow(workflow_definition)
orchestrator.get_service_status(name)
orchestrator.shutdown()
```

### 7. Base Service

**Purpose**: Foundation class for all Socratic services.

**Lifecycle**:
```
Initialization
    ↓
initialize() → Ready
    ↓
execute(action, params) → Result
    ↓
shutdown() → Stopped
```

**Key Methods**:
```python
class BaseService:
    async def initialize(self)
    async def execute(action: str, params: dict)
    async def shutdown(self)
    async def health_check(self) -> dict
    def get_status(self) -> str
```

**Pattern for Custom Services**:
```python
class MyService(BaseService):
    async def initialize(self):
        await super().initialize()
        # Custom setup

    async def execute(self, action: str, params: dict):
        if action == "analyze":
            return await self.analyze(params)
        # More actions...

    async def analyze(self, params: dict):
        # Implementation
        pass
```

## Data Flow

### Typical Request Flow

```
External Request
    ↓
ServiceMeshProxy (load balance, circuit break)
    ↓
ServiceInstance (health check, metrics)
    ↓
BaseService.execute()
    ↓
Database Operations (if needed)
    ↓
EventBus.emit() (notify other services)
    ↓
Response ↓
```

### Event Flow

```
Service A
    ↓
Emits Event to EventBus
    ↓
EventBus publishes to subscribers
    ↓
Service B handler executes
Service C handler executes
Service D handler executes
    ↓
Database updates (if handlers emit events)
```

## Cross-Service Communication

### Pattern 1: Synchronous Request-Response

```python
# Service A calls Service B through mesh
instance = lb.select_instance("service-b")
response = await proxy.call_service("service-b", "/endpoint", params=data)
```

### Pattern 2: Asynchronous Event-Driven

```python
# Service A emits event
await bus.emit(Event("analysis:complete", {"result": "..."}))

# Service B subscribes
@bus.on("analysis:complete")
async def handle_result(event):
    # Process result
```

### Pattern 3: Hybrid Workflow

```
Service A (Sync) → Service B (Sync) → Emit Event → Service C (Async)
```

## Resilience Patterns

### 1. Circuit Breaker
- Detects failing services
- Automatically opens circuit
- Prevents cascading failures
- Half-open state for recovery testing

### 2. Retry Logic
- Automatic retries with exponential backoff
- Configurable retry limits
- Failure logging

### 3. Health Checks
- Periodic health status verification
- Error rate monitoring
- Instance exclusion when unhealthy

### 4. Load Balancing
- Distributes traffic across healthy instances
- Considers instance weight and error rate
- Minimizes latency

## Deployment Architecture

```
┌─────────────────────────────────────┐
│   Load Balancer (nginx/traefik)     │
└────────────────┬────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──┐  ┌──────▼──┐  ┌─────▼───┐
│App 1 │  │  App 2  │  │  App 3  │
│ :8001│  │ :8002   │  │ :8003   │
└───┬──┘  └────┬────┘  └────┬────┘
    │         │            │
    └─────────┼────────────┘
              │
    ┌─────────▼──────────┐
    │  PostgreSQL/SQLite │
    │    Database        │
    └────────────────────┘
```

## Dependencies Between Components

```
BaseService ◄─── Orchestrator
   ▲                │
   │                │
   │                ▼
   └─────────── ConfigBuilder

ConfigBuilder
   ▲
   │
DatabaseClient ◄─── EventBus
   ▲                 │
   │                 │
   │            ┌────▼────┐
   │            │          │
   └────────────┤  BaseService
                │
                ▼
           SharedModels

ServiceMesh ◄─── LoadBalancer ◄─── ServiceMeshProxy
```

## Error Handling Strategy

```
Error Occurs
    ↓
Caught by BaseService or Middleware
    ↓
Logged with context
    ↓
EmitError Event
    ↓
Return Error Response
```

**Exception Hierarchy**:
```
SocratesError (Base)
├── DatabaseError
├── ConfigurationError
├── ValidationError
├── AuthenticationError
├── APIError
├── AgentError
├── ProjectNotFoundError
└── UserNotFoundError
```

## Extensibility

### Adding a New Service

1. Create service inheriting from `BaseService`
2. Implement `execute()` method
3. Register with `ServiceOrchestrator`
4. Optionally subscribe to relevant events

### Adding a New Event Type

1. Define event type constant
2. Emit using `EventBus.emit()`
3. Other services subscribe with `@bus.on("event:type")`

### Adding a New Entity Type

1. Define model in `shared_models.py`
2. Add table in database schema
3. Add CRUD methods to `DatabaseClient`

## Performance Considerations

1. **Asynchronous I/O**: All database and network operations are async
2. **Connection Pooling**: PostgreSQL client supports connection pooling
3. **Caching**: `@cached` decorator available for expensive operations
4. **Batch Operations**: Query multiple entities with filters instead of individual loads
5. **Event Filtering**: Event handlers can filter by event type

## Testing Strategy

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows

See test examples in `tests/` directory.

## Versioning

Socratic Core follows semantic versioning:
- MAJOR: Breaking API changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes

Current version: 0.2.0
