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

### Event Bus

```python
import asyncio
from socratic_core import EventBus

async def main():
    # Create event bus
    bus = EventBus()

    # Subscribe to events
    async def on_event(event):
        print(f"Event: {event.event_type}, Data: {event.data}")

    bus.subscribe("my_event", on_event)

    # Publish event
    await bus.publish("my_event", "my_service", {"key": "value"})

asyncio.run(main())
```

### Base Service

```python
from socratic_core import BaseService

class MyService(BaseService):
    """Custom service implementation."""

    async def initialize(self):
        """Initialize service."""
        print(f"Initializing {self.service_name}")

    async def shutdown(self):
        """Shutdown service."""
        print(f"Shutting down {self.service_name}")

    async def health_check(self):
        """Check service health."""
        return {"status": "healthy", "service": self.service_name}

# Create and use service
service = MyService("my_service", {"key": "value"})
```

## Dependencies

- **socratic-maturity**: Foundation maturity tracking
- **socratic-agents**: Multi-agent orchestration
- **pydantic**: Data validation
- **loguru**: Structured logging

## License

MIT
