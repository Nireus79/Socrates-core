"""Distributed tracing support for Socratic Core."""

import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger(__name__)


@dataclass
class SpanEvent:
    """Event within a span."""

    name: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """Distributed trace span."""

    trace_id: str
    span_id: str
    name: str
    parent_span_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    status: str = "UNSET"  # UNSET, OK, ERROR
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: list = field(default_factory=list)
    error: Optional[str] = None

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to span."""
        event = SpanEvent(name, attributes=attributes or {})
        self.events.append(event)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute."""
        self.attributes[key] = value

    def end(self, status: str = "OK", error: Optional[str] = None) -> None:
        """End the span."""
        self.end_time = datetime.utcnow()
        self.status = status
        self.error = error

        if self.start_time and self.end_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": [
                {
                    "name": event.name,
                    "timestamp": event.timestamp.isoformat(),
                    "attributes": event.attributes,
                }
                for event in self.events
            ],
            "error": self.error,
        }


class Tracer:
    """Distributed tracing system."""

    def __init__(self, service_name: str = "socratic-core"):
        """
        Initialize tracer.

        Args:
            service_name: Service name for tracing
        """
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)
        self.spans: Dict[str, Span] = {}
        self.current_trace_id: Optional[str] = None
        self.current_span_stack: list = []

    def start_trace(self, name: str) -> str:
        """
        Start a new trace.

        Args:
            name: Trace/root span name

        Returns:
            trace_id
        """
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
        )

        span.set_attribute("service", self.service_name)

        self.spans[span_id] = span
        self.current_trace_id = trace_id
        self.current_span_stack = [span_id]

        self.logger.debug(f"Started trace {trace_id} with span {span_id}")

        return trace_id

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a child span.

        Args:
            name: Span name
            attributes: Optional span attributes

        Returns:
            span_id
        """
        if not self.current_trace_id:
            raise RuntimeError("No active trace. Call start_trace() first.")

        parent_span_id = self.current_span_stack[-1] if self.current_span_stack else None

        span_id = str(uuid.uuid4())
        span = Span(
            trace_id=self.current_trace_id,
            span_id=span_id,
            name=name,
            parent_span_id=parent_span_id,
        )

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        self.spans[span_id] = span
        self.current_span_stack.append(span_id)

        self.logger.debug(f"Started span {span_id} in trace {self.current_trace_id}")

        return span_id

    def end_span(self, span_id: str, status: str = "OK", error: Optional[str] = None) -> None:
        """
        End a span.

        Args:
            span_id: Span ID
            status: Span status (OK or ERROR)
            error: Optional error message
        """
        if span_id not in self.spans:
            self.logger.warning(f"Span {span_id} not found")
            return

        span = self.spans[span_id]
        span.end(status=status, error=error)

        if self.current_span_stack and self.current_span_stack[-1] == span_id:
            self.current_span_stack.pop()

        self.logger.debug(f"Ended span {span_id} with status {status}")

    def add_event(self, span_id: str, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to span."""
        if span_id in self.spans:
            self.spans[span_id].add_event(name, attributes)

    def set_span_attribute(self, span_id: str, key: str, value: Any) -> None:
        """Set span attribute."""
        if span_id in self.spans:
            self.spans[span_id].set_attribute(key, value)

    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Generator[str, None, None]:
        """
        Context manager for spans.

        Args:
            name: Span name
            attributes: Optional span attributes

        Yields:
            span_id
        """
        span_id = self.start_span(name, attributes)
        try:
            yield span_id
            self.end_span(span_id, status="OK")
        except Exception as e:
            self.end_span(span_id, status="ERROR", error=str(e))
            raise

    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Get trace information.

        Args:
            trace_id: Trace ID

        Returns:
            Trace data with all spans
        """
        trace_spans = [
            span.to_dict() for span in self.spans.values()
            if span.trace_id == trace_id
        ]

        return {
            "trace_id": trace_id,
            "service": self.service_name,
            "span_count": len(trace_spans),
            "spans": trace_spans,
        }

    def export_jaeger(self, trace_id: str) -> Dict[str, Any]:
        """
        Export trace in Jaeger-compatible format.

        Args:
            trace_id: Trace ID

        Returns:
            Jaeger-compatible trace data
        """
        trace = self.get_trace(trace_id)

        spans = []
        for span_dict in trace["spans"]:
            spans.append({
                "traceID": trace_id,
                "spanID": span_dict["span_id"],
                "operationName": span_dict["name"],
                "references": [
                    {
                        "refType": "CHILD_OF",
                        "traceID": trace_id,
                        "spanID": span_dict["parent_span_id"],
                    }
                ] if span_dict["parent_span_id"] else [],
                "startTime": int(
                    datetime.fromisoformat(span_dict["start_time"]).timestamp() * 1_000_000
                ),
                "duration": int(span_dict["duration_ms"] * 1000),
                "tags": span_dict["attributes"],
                "logs": [
                    {
                        "timestamp": int(
                            event["timestamp"].timestamp() * 1_000_000
                        ),
                        "fields": {"message": event["name"]},
                    }
                    for event in span_dict["events"]
                ],
            })

        return {
            "batches": [
                {
                    "process": {
                        "serviceName": self.service_name,
                        "tags": {},
                    },
                    "spans": spans,
                }
            ]
        }


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "socratic-core") -> Tracer:
    """Get global tracer."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name)
    return _tracer
