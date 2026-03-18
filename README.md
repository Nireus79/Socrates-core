# Socratic Core

Core framework for building command-based CLI applications and APIs within the Socratic ecosystem.

## Overview

Socratic Core provides the foundational classes and utilities needed to build CLI applications using the Socratic framework:

- **BaseCommand** - Abstract base class for all CLI commands
- **APIResponse** - Standard response format for APIs
- Zero external dependencies (only colorama for output formatting)

## Installation

```bash
pip install socratic-core
```

## Quick Start

Create a simple command:

```python
from typing import Any, Dict, List
from socratic_core import BaseCommand

class HelloCommand(BaseCommand):
    def __init__(self):
        super().__init__(
            name="hello",
            description="Say hello",
            usage="hello <name>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        if not args:
            return self.error("Please provide a name")

        name = args[0]
        return self.success(f"Hello, {name}!")

# Use the command
cmd = HelloCommand()
result = cmd.execute(["Alice"], {})
print(result)  # {'status': 'success', 'message': 'Hello, Alice!'}
```

## Features

### BaseCommand Class

All CLI commands inherit from `BaseCommand` and implement the `execute()` method:

```python
class MyCommand(BaseCommand):
    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        # Command logic here
        return self.success("Operation completed", data={"result": value})
```

#### Response Methods

- `success(message, data)` - Create success response
- `error(message)` - Create error response
- `info(message)` - Create info response

#### Utility Methods

- `validate_args(args, min_count, max_count)` - Validate argument count
- `require_project(context)` - Check if project is loaded
- `require_user(context)` - Check if user is logged in
- `print_header(title)` - Print formatted header
- `print_section(title)` - Print formatted subsection
- `print_success(message)` - Print success message
- `print_error(message)` - Print error message
- `print_info(message)` - Print info message
- `print_warning(message)` - Print warning message

### APIResponse Class

Standard response wrapper for APIs:

```python
from socratic_core import APIResponse

response = APIResponse.success(data={"key": "value"})
# {'status': 'success', 'data': {'key': 'value'}}
```

## Usage in Other Libraries

**Socrates-CLI** uses Socratic Core for all command implementations:

```bash
pip install socrates-cli
```

**Socrates-API** uses Socratic Core for request/response handling:

```bash
pip install socrates-api
```

## Development

### Install with Development Dependencies

```bash
pip install socratic-core[dev]
```

### Run Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Lint with Ruff
ruff check src/

# Format with Black
black src/

# Type check with MyPy
mypy src/
```

## Architecture

Socratic Core is the foundation of the Socratic ecosystem:

```
socratic-core (no external dependencies)
    ↓
socrates-cli (depends on socratic-core)
    ↓
socrates-api (depends on socratic-core)
    ↓
Main Socrates project (can use all libraries)
```

## License

MIT - See LICENSE file for details

## Contributing

Contributions are welcome! Please ensure all tests pass and code is formatted with Black.
