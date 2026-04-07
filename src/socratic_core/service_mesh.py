"""Service mesh integration for distributed systems."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ServiceMetadata:
    """Metadata for a service in the mesh."""

    name: str
    version: str
    host: str
    port: int
    protocol: str = "http"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # For load balancing


@dataclass
class ServiceInstance:
    """Single instance of a service."""

    instance_id: str
    service: ServiceMetadata
    health_status: HealthStatus = HealthStatus.UNKNOWN
    last_health_check: float = 0.0
    response_time_ms: float = 0.0
    request_count: int = 0
    error_count: int = 0

    def get_error_rate(self) -> float:
        """Get service error rate."""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count


@dataclass
class CircuitBreakerState:
    """Circuit breaker state."""

    state: str = "closed"  # closed, open, half_open
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    open_time: float = 0.0
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 60


class ServiceMesh:
    """Service mesh for managing distributed services."""

    def __init__(self, mesh_name: str = "socratic_mesh"):
        """Initialize service mesh."""
        self.mesh_name = mesh_name
        self.services: Dict[str, ServiceMetadata] = {}
        self.instances: Dict[str, List[ServiceInstance]] = {}
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.logger = logging.getLogger(__name__)

    def register_service(
        self,
        name: str,
        version: str,
        host: str,
        port: int,
        protocol: str = "http",
        tags: Optional[List[str]] = None,
    ) -> ServiceMetadata:
        """
        Register a service in the mesh.

        Args:
            name: Service name
            version: Service version
            host: Service host
            port: Service port
            protocol: Protocol (http, grpc, tcp)
            tags: Service tags

        Returns:
            ServiceMetadata
        """
        service = ServiceMetadata(
            name=name,
            version=version,
            host=host,
            port=port,
            protocol=protocol,
            tags=tags or [],
        )

        self.services[name] = service
        self.instances[name] = []
        self.circuit_breakers[name] = CircuitBreakerState()

        self.logger.info(f"Registered service: {name} v{version}")
        return service

    def register_instance(
        self,
        service_name: str,
        instance_id: str,
    ) -> ServiceInstance:
        """Register a service instance."""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not registered")

        service = self.services[service_name]
        instance = ServiceInstance(
            instance_id=instance_id,
            service=service,
        )

        self.instances[service_name].append(instance)
        self.logger.debug(f"Registered instance: {instance_id} for {service_name}")
        return instance

    def check_health(self, service_name: str, instance_id: str) -> HealthStatus:
        """
        Check health of a service instance.

        Args:
            service_name: Service name
            instance_id: Instance ID

        Returns:
            HealthStatus
        """
        if service_name not in self.instances:
            return HealthStatus.UNKNOWN

        for instance in self.instances[service_name]:
            if instance.instance_id == instance_id:
                # Simulate health check
                instance.last_health_check = time.time()

                if instance.error_count > 10:
                    instance.health_status = HealthStatus.UNHEALTHY
                elif instance.get_error_rate() > 0.2:
                    instance.health_status = HealthStatus.DEGRADED
                else:
                    instance.health_status = HealthStatus.HEALTHY

                return instance.health_status

        return HealthStatus.UNKNOWN

    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get all healthy instances of a service."""
        if service_name not in self.instances:
            return []

        return [i for i in self.instances[service_name] if i.health_status == HealthStatus.HEALTHY]

    def get_available_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get available instances (healthy + degraded)."""
        if service_name not in self.instances:
            return []

        return [
            i
            for i in self.instances[service_name]
            if i.health_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        ]

    def record_request(
        self,
        service_name: str,
        instance_id: str,
        response_time_ms: float,
        is_error: bool = False,
    ) -> None:
        """Record a request to a service instance."""
        if service_name not in self.instances:
            return

        for instance in self.instances[service_name]:
            if instance.instance_id == instance_id:
                instance.request_count += 1
                instance.response_time_ms = response_time_ms
                if is_error:
                    instance.error_count += 1

                # Update circuit breaker
                cb = self.circuit_breakers[service_name]
                if is_error:
                    cb.failure_count += 1
                    cb.last_failure_time = time.time()
                    if cb.failure_count >= cb.failure_threshold:
                        cb.state = "open"
                else:
                    if cb.state == "half_open":
                        cb.success_count += 1
                        if cb.success_count >= cb.success_threshold:
                            cb.state = "closed"
                            cb.failure_count = 0
                break

    def should_circuit_break(self, service_name: str) -> bool:
        """Check if circuit breaker is open for service."""
        if service_name not in self.circuit_breakers:
            return False

        cb = self.circuit_breakers[service_name]

        if cb.state == "open":
            elapsed = time.time() - cb.open_time
            if elapsed > cb.timeout_seconds:
                cb.state = "half_open"
                cb.success_count = 0
                return False
            return True

        return False

    def get_mesh_status(self) -> Dict[str, Any]:
        """Get overall mesh status."""
        total_services = len(self.services)
        total_instances = sum(len(i) for i in self.instances.values())
        healthy_instances = sum(
            len([inst for inst in instances if inst.health_status == HealthStatus.HEALTHY])
            for instances in self.instances.values()
        )

        return {
            "mesh_name": self.mesh_name,
            "total_services": total_services,
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "health_percentage": (
                (healthy_instances / total_instances * 100) if total_instances > 0 else 0
            ),
            "services": {
                name: {
                    "version": svc.version,
                    "instances": len(self.instances.get(name, [])),
                    "healthy": len(
                        [
                            i
                            for i in self.instances.get(name, [])
                            if i.health_status == HealthStatus.HEALTHY
                        ]
                    ),
                }
                for name, svc in self.services.items()
            },
        }


class LoadBalancer:
    """Load balancer for service instances."""

    def __init__(self, mesh: ServiceMesh):
        """Initialize load balancer."""
        self.mesh = mesh
        self.round_robin_index: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)

    def select_instance(
        self,
        service_name: str,
        strategy: str = "round_robin",
    ) -> Optional[ServiceInstance]:
        """
        Select an instance using specified strategy.

        Args:
            service_name: Service name
            strategy: Selection strategy (round_robin, least_connections, random, weighted)

        Returns:
            Selected ServiceInstance or None
        """
        available = self.mesh.get_available_instances(service_name)
        if not available:
            return None

        if strategy == "round_robin":
            idx = self.round_robin_index.get(service_name, 0)
            selected = available[idx % len(available)]
            self.round_robin_index[service_name] = (idx + 1) % len(available)
            return selected

        elif strategy == "least_connections":
            return min(available, key=lambda i: i.request_count)

        elif strategy == "random":
            import random

            return random.choice(available)

        elif strategy == "weighted":
            # Weighted by inverse of error rate
            weights = [max(1 - i.get_error_rate(), 0.1) * i.service.weight for i in available]
            total = sum(weights)
            if total == 0:
                return available[0]

            import random

            r = random.uniform(0, total)
            current = 0
            for instance, weight in zip(available, weights):
                current += weight
                if r <= current:
                    return instance
            return available[-1]

        return available[0]


class ServiceMeshProxy:
    """Proxy for intercepting service calls."""

    def __init__(self, mesh: ServiceMesh, load_balancer: LoadBalancer):
        """Initialize proxy."""
        self.mesh = mesh
        self.load_balancer = load_balancer
        self.interceptors: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)

    def register_interceptor(
        self,
        service_name: str,
        interceptor: Callable,
    ) -> None:
        """Register an interceptor for a service."""
        if service_name not in self.interceptors:
            self.interceptors[service_name] = []
        self.interceptors[service_name].append(interceptor)

    async def call_service(
        self,
        service_name: str,
        endpoint: str,
        **kwargs,
    ) -> Any:
        """
        Make a call to a service through the mesh.

        Args:
            service_name: Target service name
            endpoint: Endpoint to call
            **kwargs: Request parameters

        Returns:
            Response from service
        """
        # Check circuit breaker
        if self.mesh.should_circuit_break(service_name):
            raise RuntimeError(f"Circuit breaker open for {service_name}")

        # Select instance
        instance = self.load_balancer.select_instance(service_name)
        if not instance:
            raise RuntimeError(f"No available instances for {service_name}")

        # Run interceptors
        for interceptor in self.interceptors.get(service_name, []):
            await interceptor(instance, endpoint, kwargs)

        # Make request and record metrics
        start = time.time()
        try:
            # Simulate service call
            response = await asyncio.sleep(0.01)  # Placeholder
            duration = (time.time() - start) * 1000
            self.mesh.record_request(
                service_name,
                instance.instance_id,
                duration,
                is_error=False,
            )
            return response
        except Exception:
            duration = (time.time() - start) * 1000
            self.mesh.record_request(
                service_name,
                instance.instance_id,
                duration,
                is_error=True,
            )
            raise
