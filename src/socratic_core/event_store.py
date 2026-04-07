"""Event persistence for socratic-core."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events."""

    USER_CREATED = "user_created"
    QUESTION_ASKED = "question_asked"
    ANSWER_SUBMITTED = "answer_submitted"
    LEARNING_PATH_UPDATED = "learning_path_updated"
    SKILL_EVALUATED = "skill_evaluated"


@dataclass
class DomainEvent:
    """Base domain event."""

    event_id: str
    event_type: EventType
    aggregate_id: str
    timestamp: datetime
    data: Dict[str, Any]
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "version": self.version,
        }


class EventStore:
    """Stores and retrieves events."""

    def __init__(self):
        self.events: List[DomainEvent] = []
        self.snapshots: Dict[str, DomainEvent] = {}
        self.subscribers: Dict[EventType, List] = {}
        self.lock = asyncio.Lock()

    async def append_event(self, event: DomainEvent) -> None:
        """Append event to store."""
        async with self.lock:
            self.events.append(event)

        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                await self._call_callback(callback, event)

    async def _call_callback(self, callback, event):
        if asyncio.iscoroutinefunction(callback):
            await callback(event)
        else:
            callback(event)

    async def get_events(self, aggregate_id: str) -> List[DomainEvent]:
        """Get all events for an aggregate."""
        return [e for e in self.events if e.aggregate_id == aggregate_id]

    async def get_events_since(self, aggregate_id: str, version: int) -> List[DomainEvent]:
        """Get events since a specific version."""
        return [e for e in self.events if e.aggregate_id == aggregate_id and e.version > version]

    async def get_events_by_type(self, event_type: EventType) -> List[DomainEvent]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]

    async def replay_events(self, aggregate_id: str) -> List[Dict[str, Any]]:
        """Replay all events for an aggregate."""
        events = await self.get_events(aggregate_id)
        return [e.to_dict() for e in events]

    async def subscribe(self, event_type: EventType, callback) -> None:
        """Subscribe to events of a type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def snapshot(self, aggregate_id: str, event: DomainEvent) -> None:
        """Create a snapshot of aggregate state."""
        self.snapshots[aggregate_id] = event

    async def get_snapshot(self, aggregate_id: str) -> Optional[DomainEvent]:
        """Retrieve snapshot for an aggregate."""
        return self.snapshots.get(aggregate_id)

    async def get_event_count(self) -> int:
        """Get total event count."""
        return len(self.events)

    async def export_events(self, aggregate_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Export events to dictionary format."""
        events = await self.get_events(aggregate_id) if aggregate_id else self.events
        return [e.to_dict() for e in events]

    async def clear_events(self) -> None:
        """Clear all events."""
        async with self.lock:
            self.events.clear()
            self.snapshots.clear()


class EventFilter:
    """Filter events by various criteria."""

    def __init__(self, events: List[DomainEvent]):
        self.events = events

    def by_type(self, event_type: EventType) -> "EventFilter":
        self.events = [e for e in self.events if e.event_type == event_type]
        return self

    def by_aggregate(self, aggregate_id: str) -> "EventFilter":
        self.events = [e for e in self.events if e.aggregate_id == aggregate_id]
        return self

    def by_time_range(self, start: datetime, end: datetime) -> "EventFilter":
        self.events = [e for e in self.events if start <= e.timestamp <= end]
        return self

    def by_data_field(self, field: str, value: Any) -> "EventFilter":
        self.events = [e for e in self.events if e.data.get(field) == value]
        return self

    def get_results(self) -> List[DomainEvent]:
        return self.events
