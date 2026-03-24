# Socratic Core

Core services for the Socratic system: event bus, orchestrator, base services, and shared models.

## Features

- **EventBus**: Event-driven architecture for system-wide communication
- **BaseService**: Foundation class for all services
- **Orchestrator**: Core orchestration logic
- **SharedModels**: Common data structures used across the system

## Installation

```bash
pip install socratic-core
```

## Quick Start

```python
from socratic_core import EventBus, BaseService

# Create event bus
bus = EventBus()

# Subscribe to events
def on_event(event_type, data):
    print(f"Event: {event_type}, Data: {data}")

bus.subscribe("my_event", on_event)

# Emit event
bus.emit("my_event", {"key": "value"})
```

## Dependencies

- **socratic-maturity**: Foundation maturity tracking
- **socratic-agents**: Multi-agent orchestration
- **pydantic**: Data validation
- **loguru**: Structured logging

## License

MIT
