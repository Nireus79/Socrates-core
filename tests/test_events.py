"""Tests for event system."""

import pytest

from socratic_core.events.emitter import EventEmitter
from socratic_core.events.event_types import EventType


class TestEventEmitter:
    """Test EventEmitter basic functionality."""

    def test_emitter_creation(self):
        """Test creating an EventEmitter."""
        emitter = EventEmitter()
        assert emitter is not None

    def test_event_registration(self):
        """Test registering an event listener."""
        emitter = EventEmitter()
        called = []

        def handler(data):
            called.append(True)

        emitter.on(EventType.LOG_INFO, handler)
        emitter.emit(EventType.LOG_INFO, {})

        assert len(called) == 1

    def test_multiple_listeners(self):
        """Test multiple listeners for same event."""
        emitter = EventEmitter()
        results = []

        def handler1(data):
            results.append("h1")

        def handler2(data):
            results.append("h2")

        emitter.on(EventType.LOG_INFO, handler1)
        emitter.on(EventType.LOG_INFO, handler2)

        emitter.emit(EventType.LOG_INFO, {})

        assert len(results) == 2
        assert "h1" in results
        assert "h2" in results

    def test_event_isolation(self):
        """Test different event types don't interfere."""
        emitter = EventEmitter()
        results = []

        def handler1(data):
            results.append("info")

        def handler2(data):
            results.append("debug")

        emitter.on(EventType.LOG_INFO, handler1)
        emitter.on(EventType.LOG_DEBUG, handler2)

        emitter.emit(EventType.LOG_INFO, {})
        assert results == ["info"]

        emitter.emit(EventType.LOG_DEBUG, {})
        assert results == ["info", "debug"]

    def test_emit_without_listeners(self):
        """Test emitting event without listeners doesn't crash."""
        emitter = EventEmitter()
        # Should not raise
        emitter.emit(EventType.LOG_INFO, {"test": "data"})

    def test_once_listener(self):
        """Test once() listener fires only once."""
        emitter = EventEmitter()
        called = []

        def handler(data):
            called.append(True)

        emitter.once(EventType.LOG_INFO, handler)

        emitter.emit(EventType.LOG_INFO, {})
        emitter.emit(EventType.LOG_INFO, {})

        # Should only be called once
        assert len(called) == 1

    def test_listener_count(self):
        """Test listener_count method."""
        emitter = EventEmitter()

        def handler1(data):
            pass

        def handler2(data):
            pass

        emitter.on(EventType.LOG_INFO, handler1)
        emitter.on(EventType.LOG_INFO, handler2)

        count = emitter.listener_count(EventType.LOG_INFO)
        assert count == 2

    def test_remove_listener(self):
        """Test removing a listener."""
        emitter = EventEmitter()
        called = []

        def handler(data):
            called.append(True)

        emitter.on(EventType.LOG_INFO, handler)
        emitter.emit(EventType.LOG_INFO, {})
        assert len(called) == 1

        emitter.remove_listener(EventType.LOG_INFO, handler)
        emitter.emit(EventType.LOG_INFO, {})

        # Should not be called again
        assert len(called) == 1

    def test_remove_all_listeners(self):
        """Test removing all listeners for an event."""
        emitter = EventEmitter()
        called = []

        def handler1(data):
            called.append("h1")

        def handler2(data):
            called.append("h2")

        emitter.on(EventType.LOG_INFO, handler1)
        emitter.on(EventType.LOG_INFO, handler2)

        emitter.emit(EventType.LOG_INFO, {})
        assert len(called) == 2

        emitter.remove_all_listeners(EventType.LOG_INFO)
        emitter.emit(EventType.LOG_INFO, {})

        # Should not be called again
        assert len(called) == 2

    def test_event_names(self):
        """Test getting all event names with listeners."""
        emitter = EventEmitter()

        def handler(data):
            pass

        emitter.on(EventType.LOG_INFO, handler)
        emitter.on(EventType.LOG_DEBUG, handler)

        names = emitter.get_event_names()

        assert EventType.LOG_INFO in names
        assert EventType.LOG_DEBUG in names


class TestAsyncEventEmitter:
    """Test async event handling."""

    @pytest.mark.asyncio
    async def test_async_listener(self):
        """Test async listener."""
        emitter = EventEmitter()
        called = []

        async def async_handler(data):
            called.append(True)

        emitter.on_async(EventType.LOG_INFO, async_handler)

        # Async emission
        await emitter.emit_async(EventType.LOG_INFO, {})

        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_multiple_async_listeners(self):
        """Test multiple async listeners."""
        emitter = EventEmitter()
        results = []

        async def handler1(data):
            results.append("h1")

        async def handler2(data):
            results.append("h2")

        emitter.on_async(EventType.LOG_INFO, handler1)
        emitter.on_async(EventType.LOG_INFO, handler2)

        await emitter.emit_async(EventType.LOG_INFO, {})

        assert len(results) == 2


class TestEventType:
    """Test EventType enum."""

    def test_event_types_exist(self):
        """Test that common event types exist."""
        assert hasattr(EventType, "LOG_INFO")
        assert hasattr(EventType, "LOG_DEBUG")
        assert hasattr(EventType, "LOG_ERROR")

    def test_event_type_values(self):
        """Test event type values are strings."""
        assert isinstance(EventType.LOG_INFO.value, str)

    def test_event_type_count(self):
        """Test that we have a reasonable number of event types."""
        event_types = [e for e in EventType]
        assert len(event_types) > 0
        assert len(event_types) < 200  # Reasonable upper bound
