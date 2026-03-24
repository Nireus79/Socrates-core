"""Tests for core module."""

import pytest

from socratic_core.event_bus import EventBus


class TestEventBus:
    """Test EventBus functionality."""

    def test_event_bus_creation(self):
        """EventBus should initialize without errors."""
        bus = EventBus()
        assert bus is not None

    def test_event_subscription(self):
        """Should subscribe to events."""
        bus = EventBus()
        called = []

        def handler(data):
            called.append(data)

        bus.subscribe("test_event", handler)
        assert len(bus._subscribers.get("test_event", [])) > 0

    @pytest.mark.asyncio
    async def test_event_emission(self):
        """Should emit events to subscribers."""
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe("test_event", handler)
        await bus.publish("test_event", "test_service", {"key": "value"})

        assert len(received) > 0
        assert received[0].event_type == "test_event"
