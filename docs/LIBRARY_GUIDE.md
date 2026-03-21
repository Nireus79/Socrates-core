# socratic-core Library Guide

## Overview

**socratic-core** is the foundational framework library for the entire Socrates AI ecosystem. It provides zero-dependency core components that all other Socrates packages depend on.

**Current Version**: 0.1.1
**Python Support**: 3.8+
**License**: MIT
**Status**: Production Ready

## What This Library Does

socratic-core is a lightweight, dependency-free framework providing:

### 1. Configuration Management (`SocratesConfig`)
- Centralized configuration from environment variables
- Type-safe configuration with Pydantic
- Support for multiple environments (dev, staging, production)
- Configuration inheritance and overrides

### 2. Event System
- **EventEmitter** - Publish-subscribe event dispatcher
- **90+ Event Types** - Predefined events for all major operations
- Sync and async listener support
- Event filtering and prioritization

**Event Categories**:
- Lifecycle events (AGENT_START, AGENT_COMPLETE, AGENT_ERROR)
- Project events (PROJECT_CREATED, PROJECT_SAVED, PROJECT_DELETED)
- Knowledge events (KNOWLEDGE_LOADED, DOCUMENT_IMPORTED)
- Code events (CODE_GENERATED, CODE_ANALYSIS_COMPLETE)
- System events (SYSTEM_INITIALIZED, TOKEN_USAGE)
- Learning events (LEARNING_METRICS_UPDATED)

### 3. Exception Hierarchy
- **SocratesError** - Base exception class
- 8 specialized exception types for different error scenarios
- Structured error handling across the ecosystem
- Exception types:
  - ConfigurationError
  - AuthenticationError
  - ValidationError
  - ResourceNotFoundError
  - OperationError
  - TimeoutError
  - RateLimitError
  - SecurityError

### 4. Logging Infrastructure
- **LoggingConfig** - Centralized logging configuration
- **JsonFormatter** - Structured JSON logging for ELK/Splunk integration
- **PerformanceMonitor** - Track operation performance
- Configurable log levels and outputs

### 5. Utilities
- **ID Generators** - Generate unique, traceable IDs
- **TTL Cache** - Time-to-live based in-memory caching
- **Datetime Helpers** - Consistent timezone handling (UTC-first)
- **Type Helpers** - Pydantic models and validators

## Architecture

```
socratic-core
    │
    ├── config/        # Configuration system
    ├── events/        # Event system
    ├── exceptions/    # Exception hierarchy
    ├── logging/       # Logging infrastructure
    └── utils/         # Utilities and helpers
```

## Key Classes

### SocratesConfig
```python
from socratic_core import SocratesConfig

# Load from environment
config = SocratesConfig.from_env()

# Or create directly
config = SocratesConfig(
    data_dir="/data/socrates",
    log_level="DEBUG",
    max_workers=4
)

# Use config
print(config.data_dir)
print(config.log_level)
```

### EventEmitter
```python
from socratic_core import EventEmitter, EventType

emitter = EventEmitter()

# Register listener
def on_project_created(event_data):
    print(f"Project created: {event_data}")

emitter.on(EventType.PROJECT_CREATED, on_project_created)

# Emit event
emitter.emit(EventType.PROJECT_CREATED, {"project_id": "123"})

# Async listeners
async def on_agent_complete(event_data):
    await process_results(event_data)

emitter.on(EventType.AGENT_COMPLETE, on_agent_complete)
```

### Exception Handling
```python
from socratic_core import SocratesError, ValidationError

try:
    if not is_valid(data):
        raise ValidationError("Invalid input data")
except SocratesError as e:
    logger.error(f"Socrates error: {e}")
```

### Logging
```python
from socratic_core import LoggingConfig, get_logger

# Configure logging
config = LoggingConfig(
    level="INFO",
    json_format=True,
    output="file"
)
config.setup()

# Get logger
logger = get_logger(__name__)
logger.info("Application started")
```

## Usage Patterns

### In a New Service
```python
from socratic_core import SocratesConfig, EventEmitter, get_logger

# 1. Load configuration
config = SocratesConfig.from_env()

# 2. Setup logging
config.setup_logging()
logger = get_logger(__name__)

# 3. Create event system
event_emitter = EventEmitter()

# 4. Register event listeners
event_emitter.on(EventType.AGENT_START, on_agent_start)
event_emitter.on(EventType.AGENT_ERROR, on_agent_error)

# 5. Use in your service
def run_agent(agent_id):
    event_emitter.emit(EventType.AGENT_START, {"agent_id": agent_id})
    try:
        result = agent.run()
        event_emitter.emit(EventType.AGENT_COMPLETE, {"result": result})
    except Exception as e:
        event_emitter.emit(EventType.AGENT_ERROR, {"error": str(e)})
```

### In a New Library (Optional Dependency)
```python
# socratic-core is always imported, never optional
from socratic_core import SocratesConfig, EventEmitter

class MyLibraryService:
    def __init__(self, config: SocratesConfig, emitter: EventEmitter):
        self.config = config
        self.emitter = emitter

    def process(self):
        self.emitter.emit(EventType.CUSTOM_EVENT, {"data": "..."})
```

## Environment Variables

### Core
- `SOCRATES_DATA_DIR` - Data storage directory (default: ~/.socrates)
- `SOCRATES_LOG_LEVEL` - Logging level (default: INFO)
- `SOCRATES_LOG_FORMAT` - Logging format: text or json (default: text)
- `SOCRATES_ENVIRONMENT` - Environment: dev, staging, production (default: dev)

### Logging
- `SOCRATES_LOG_FILE` - Path to log file (optional)
- `SOCRATES_LOG_JSON` - Enable JSON logging (default: false)
- `SOCRATES_LOG_METRICS` - Enable metrics logging (default: true)

## Dependencies

**ZERO external dependencies!**

socratic-core is intentionally lightweight with no external dependencies beyond Python stdlib. This ensures:
- Fast installation
- No dependency conflicts
- Minimal attack surface
- Works in restricted environments

## Integration with Other Packages

### Required By All
Every package in the Socrates ecosystem depends on socratic-core:
- socratic-agents
- socratic-rag
- socratic-analyzer
- socratic-learning
- socratic-workflow
- socratic-knowledge
- socratic-conflict
- socrates-ai (main wrapper)
- socrates-cli
- socrates-core-api
- socrates-ai-langraph
- socrates-ai-openclaw

### Use Case: Building New Packages
When creating a new Socrates package:

1. **Always import from socratic-core**:
   ```python
   from socratic_core import SocratesConfig, EventEmitter, get_logger
   ```

2. **Use SocratesConfig for configuration**
3. **Emit events via EventEmitter**
4. **Use logger from get_logger()**
5. **Raise SocratesError subclasses**

## Best Practices

### 1. Configuration
- Load once at startup: `config = SocratesConfig.from_env()`
- Pass config to all services
- Never hardcode configuration
- Use environment variables for secrets

### 2. Events
- Emit events for all significant operations
- Use appropriate EventType
- Include relevant data in event payload
- Subscribe to events you care about
- Don't assume event listener order

### 3. Logging
- Use get_logger(__name__) in each module
- Log at appropriate level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include context in log messages
- Don't log sensitive data (API keys, passwords)

### 4. Exceptions
- Raise specific SocratesError subclasses
- Include meaningful error messages
- Chain exceptions with `raise ... from e`
- Handle SocratesError at service boundaries

## Common Patterns

### Configuration + Logging Setup
```python
from socratic_core import SocratesConfig

config = SocratesConfig.from_env()
config.setup_logging()
```

### Event-Driven Service
```python
from socratic_core import EventEmitter, EventType

emitter = EventEmitter()
emitter.on(EventType.PROJECT_CREATED, handle_project_creation)
emitter.emit(EventType.PROJECT_CREATED, project_data)
```

### Error Handling
```python
from socratic_core import SocratesError, get_logger

logger = get_logger(__name__)

try:
    do_something()
except SocratesError as e:
    logger.error(f"Failed: {e}")
```

## Testing

All packages should import from socratic-core in tests:

```python
import pytest
from socratic_core import SocratesConfig, EventEmitter

@pytest.fixture
def config():
    return SocratesConfig(data_dir="/tmp/test")

@pytest.fixture
def emitter():
    return EventEmitter()

def test_something(config, emitter):
    # Your test here
    pass
```

## Migration Guide

### From Direct Configuration to SocratesConfig
```python
# Before
data_dir = os.getenv("DATA_DIR", "/tmp")
log_level = os.getenv("LOG_LEVEL", "INFO")

# After
config = SocratesConfig.from_env()
data_dir = config.data_dir
log_level = config.log_level
```

### From Print Statements to Logger
```python
# Before
print("Agent started")

# After
from socratic_core import get_logger
logger = get_logger(__name__)
logger.info("Agent started")
```

### From Custom Events to EventType
```python
# Before
callbacks = {"on_complete": [...]}
for cb in callbacks["on_complete"]:
    cb(result)

# After
from socratic_core import EventEmitter, EventType
emitter = EventEmitter()
emitter.on(EventType.AGENT_COMPLETE, callback)
emitter.emit(EventType.AGENT_COMPLETE, result)
```

## Troubleshooting

### Configuration Not Loading
```python
from socratic_core import SocratesConfig

# Check environment
import os
print(os.getenv("SOCRATES_DATA_DIR"))

# Load with defaults
config = SocratesConfig.from_env()
print(config.data_dir)
```

### Events Not Firing
```python
from socratic_core import EventEmitter, EventType

emitter = EventEmitter()

# Make sure listener is registered BEFORE emit
emitter.on(EventType.AGENT_START, my_handler)

# Then emit
emitter.emit(EventType.AGENT_START, data)
```

### Logging Not Appearing
```python
from socratic_core import SocratesConfig, get_logger

# Setup logging
config = SocratesConfig.from_env()
config.setup_logging()

# Then get logger
logger = get_logger(__name__)
logger.info("This should appear")
```

## Version History

### v0.1.1 (Current)
- Stable configuration system
- 90+ event types
- 8 exception types
- Performance monitoring
- JSON logging support

### v0.1.0
- Initial release
- Basic configuration
- Event system
- Exception hierarchy

## Contributing

When modifying socratic-core:
1. Ensure zero external dependencies
2. Update event types if adding new events
3. Update exception types if adding new errors
4. Maintain backward compatibility
5. Update tests
6. Update this documentation

## Related Documentation

- [Socrates Ecosystem Architecture](../../docs/SOCRATES_ECOSYSTEM_ARCHITECTURE.md)
- [Configuration Guide](./CONFIGURATION.md) (if exists)
- [Events Reference](./EVENTS.md) (if exists)

## Support

For issues or questions:
- GitHub Issues: https://github.com/Nireus79/Socrates/issues
- Documentation: https://github.com/Nireus79/Socrates/tree/main/Socrates-core/docs
