"""Comprehensive metrics collection and reporting for Socratic Core."""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """A single metric measurement."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "unit": self.unit,
        }


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""

    name: str
    count: int = 0
    total: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")
    avg: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0

    @property
    def mean(self) -> float:
        """Get mean/average."""
        return self.total / self.count if self.count > 0 else 0.0

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MetricSummary({self.name}, count={self.count}, "
            f"avg={self.avg:.3f}, min={self.min:.3f}, max={self.max:.3f})"
        )


class Counter:
    """Simple counter metric."""

    def __init__(self, name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None):
        """
        Initialize counter.

        Args:
            name: Metric name
            help_text: Help text for documentation
            labels: Label names
        """
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self.value = 0.0
        self.timestamp = datetime.utcnow()

    def inc(self, amount: float = 1.0) -> None:
        """Increment counter."""
        self.value += amount
        self.timestamp = datetime.utcnow()

    def get(self) -> float:
        """Get current value."""
        return self.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": "counter",
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
        }


class Gauge:
    """Gauge metric that can go up or down."""

    def __init__(self, name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None):
        """
        Initialize gauge.

        Args:
            name: Metric name
            help_text: Help text for documentation
            labels: Label names
        """
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self.value = 0.0
        self.timestamp = datetime.utcnow()

    def set(self, value: float) -> None:
        """Set gauge value."""
        self.value = value
        self.timestamp = datetime.utcnow()

    def inc(self, amount: float = 1.0) -> None:
        """Increment gauge."""
        self.value += amount
        self.timestamp = datetime.utcnow()

    def dec(self, amount: float = 1.0) -> None:
        """Decrement gauge."""
        self.value -= amount
        self.timestamp = datetime.utcnow()

    def get(self) -> float:
        """Get current value."""
        return self.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": "gauge",
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
        }


class Histogram:
    """Histogram metric for value distributions."""

    def __init__(
        self,
        name: str,
        help_text: str = "",
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize histogram.

        Args:
            name: Metric name
            help_text: Help text for documentation
            buckets: Bucket boundaries (default: standard HTTP latency buckets)
            labels: Label names
        """
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self.bucket_counts = {bucket: 0 for bucket in self.buckets}
        self.bucket_counts[float("inf")] = 0
        self.sum = 0.0
        self.count = 0

    def observe(self, value: float) -> None:
        """Observe a value."""
        self.sum += value
        self.count += 1

        # Update bucket counts
        for bucket in self.buckets:
            if value <= bucket:
                self.bucket_counts[bucket] += 1
        self.bucket_counts[float("inf")] += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": "histogram",
            "name": self.name,
            "sum": self.sum,
            "count": self.count,
            "buckets": self.bucket_counts,
            "labels": self.labels,
        }


class MetricsRegistry:
    """Central registry for all metrics."""

    def __init__(self):
        """Initialize metrics registry."""
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.logger = logging.getLogger(__name__)

    def register_counter(self, name: str, help_text: str = "") -> Counter:
        """Register a counter."""
        if name not in self.counters:
            self.counters[name] = Counter(name, help_text)
        return self.counters[name]

    def register_gauge(self, name: str, help_text: str = "") -> Gauge:
        """Register a gauge."""
        if name not in self.gauges:
            self.gauges[name] = Gauge(name, help_text)
        return self.gauges[name]

    def register_histogram(
        self,
        name: str,
        help_text: str = "",
        buckets: Optional[List[float]] = None,
    ) -> Histogram:
        """Register a histogram."""
        if name not in self.histograms:
            self.histograms[name] = Histogram(name, help_text, buckets)
        return self.histograms[name]

    def get_counter(self, name: str) -> Optional[Counter]:
        """Get a counter by name."""
        return self.counters.get(name)

    def get_gauge(self, name: str) -> Optional[Gauge]:
        """Get a gauge by name."""
        return self.gauges.get(name)

    def get_histogram(self, name: str) -> Optional[Histogram]:
        """Get a histogram by name."""
        return self.histograms.get(name)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Export counters
        for counter in self.counters.values():
            lines.append(f"# HELP {counter.name} {counter.help_text}")
            lines.append(f"# TYPE {counter.name} counter")
            labels_str = self._format_labels(counter.labels)
            lines.append(f"{counter.name}{labels_str} {counter.value}")

        # Export gauges
        for gauge in self.gauges.values():
            lines.append(f"# HELP {gauge.name} {gauge.help_text}")
            lines.append(f"# TYPE {gauge.name} gauge")
            labels_str = self._format_labels(gauge.labels)
            lines.append(f"{gauge.name}{labels_str} {gauge.value}")

        # Export histograms
        for histogram in self.histograms.values():
            lines.append(f"# HELP {histogram.name} {histogram.help_text}")
            lines.append(f"# TYPE {histogram.name} histogram")
            labels_str = self._format_labels(histogram.labels)

            for bucket, count in histogram.bucket_counts.items():
                if bucket == float("inf"):
                    bucket_str = "+Inf"
                else:
                    bucket_str = str(bucket)
                lines.append(
                    f'{histogram.name}_bucket{{le="{bucket_str}"{labels_str}}} {count}'
                )

            lines.append(f'{histogram.name}_sum{labels_str} {histogram.sum}')
            lines.append(f'{histogram.name}_count{labels_str} {histogram.count}')

        return "\n".join(lines)

    def export_json(self) -> Dict[str, Any]:
        """Export metrics as JSON."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "counters": {name: counter.to_dict() for name, counter in self.counters.items()},
            "gauges": {name: gauge.to_dict() for name, gauge in self.gauges.items()},
            "histograms": {name: hist.to_dict() for name, hist in self.histograms.items()},
        }

    @staticmethod
    def _format_labels(labels: Dict[str, str]) -> str:
        """Format labels for Prometheus output."""
        if not labels:
            return ""
        label_strs = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(label_strs) + "}"


class Timer:
    """Context manager for timing operations."""

    def __init__(self, histogram: Histogram, labels: Optional[Dict[str, str]] = None):
        """
        Initialize timer.

        Args:
            histogram: Histogram to record timing to
            labels: Optional labels to attach
        """
        self.histogram = histogram
        self.labels = labels or {}
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and record."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.histogram.observe(duration)


class MetricsCollector:
    """Comprehensive metrics collection system."""

    def __init__(self):
        """Initialize metrics collector."""
        self.registry = MetricsRegistry()
        self.logger = logging.getLogger(__name__)

        # Initialize standard metrics
        self._init_standard_metrics()

    def _init_standard_metrics(self) -> None:
        """Initialize standard metrics."""
        # Request metrics
        self.registry.register_counter(
            "socratic_requests_total",
            "Total number of requests",
        )
        self.registry.register_histogram(
            "socratic_request_duration_seconds",
            "Request duration in seconds",
        )
        self.registry.register_gauge(
            "socratic_active_requests",
            "Number of active requests",
        )

        # Error metrics
        self.registry.register_counter(
            "socratic_errors_total",
            "Total number of errors",
        )
        self.registry.register_gauge(
            "socratic_error_rate",
            "Current error rate",
        )

        # Cache metrics
        self.registry.register_counter(
            "socratic_cache_hits_total",
            "Total cache hits",
        )
        self.registry.register_counter(
            "socratic_cache_misses_total",
            "Total cache misses",
        )
        self.registry.register_gauge(
            "socratic_cache_size_bytes",
            "Cache size in bytes",
        )

        # Processing metrics
        self.registry.register_histogram(
            "socratic_processing_duration_seconds",
            "Processing duration in seconds",
        )
        self.registry.register_counter(
            "socratic_items_processed_total",
            "Total items processed",
        )

    def record_request(self, endpoint: str, method: str, duration_ms: float) -> None:
        """Record an API request."""
        self.registry.get_counter("socratic_requests_total").inc()
        histogram = self.registry.get_histogram("socratic_request_duration_seconds")
        if histogram:
            histogram.observe(duration_ms / 1000)

    def record_error(self, error_type: str) -> None:
        """Record an error."""
        self.registry.get_counter("socratic_errors_total").inc()

    def record_cache_hit(self) -> None:
        """Record cache hit."""
        self.registry.get_counter("socratic_cache_hits_total").inc()

    def record_cache_miss(self) -> None:
        """Record cache miss."""
        self.registry.get_counter("socratic_cache_misses_total").inc()

    def set_cache_size(self, size_bytes: int) -> None:
        """Set current cache size."""
        gauge = self.registry.get_gauge("socratic_cache_size_bytes")
        if gauge:
            gauge.set(size_bytes)

    def get_metrics_prometheus(self) -> str:
        """Get metrics in Prometheus format."""
        return self.registry.export_prometheus()

    def get_metrics_json(self) -> Dict[str, Any]:
        """Get metrics as JSON."""
        return self.registry.export_json()

    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        hits = self.registry.get_counter("socratic_cache_hits_total")
        misses = self.registry.get_counter("socratic_cache_misses_total")

        if hits and misses:
            total = hits.get() + misses.get()
            return hits.get() / total if total > 0 else 0.0

        return 0.0

    def get_error_rate(self) -> float:
        """Calculate error rate."""
        total_requests = self.registry.get_counter("socratic_requests_total")
        total_errors = self.registry.get_counter("socratic_errors_total")

        if total_requests and total_errors:
            total = total_requests.get()
            return total_errors.get() / total if total > 0 else 0.0

        return 0.0


# Global metrics instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
