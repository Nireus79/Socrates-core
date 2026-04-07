"""
ServiceOrchestrator - Central orchestrator for managing all services.

Responsible for:
- Starting/stopping all services with dependency ordering
- Routing requests between services
- Managing service dependencies
- Health monitoring
- Event-driven inter-service communication
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from socratic_core.base_service import BaseService
from socratic_core.event_bus import EventBus


class ServiceOrchestrator:
    """Orchestrates all services in the platform."""

    # Dependency map: service -> list of services it depends on
    DEPENDENCIES = {
        "foundation": [],
        "knowledge": ["foundation"],
        "learning": ["foundation"],
        "agents": ["foundation", "learning"],
        "workflow": ["foundation", "agents"],
        "analytics": ["foundation"],
    }

    # Startup order based on dependencies
    STARTUP_ORDER = [
        "foundation",
        "knowledge",
        "learning",
        "agents",
        "analytics",
        "workflow",
    ]

    def __init__(self):
        """Initialize orchestrator."""
        self._services: Dict[str, BaseService] = {}
        self.event_bus = EventBus()
        self._started_services: List[str] = []
        self.logger = logging.getLogger("socrates.orchestrator")

    @property
    def services(self) -> Dict[str, BaseService]:
        """Get registered services."""
        return self._services

    def register_service(self, service: BaseService) -> None:
        """
        Register a service with the orchestrator.

        Args:
            service: Service instance to register
        """
        self._services[service.service_name] = service

        # Inject orchestrator for inter-service communication
        service.set_orchestrator(self)

        # Inject event bus into service if it has the set_event_bus method
        if hasattr(service, "set_event_bus"):
            service.set_event_bus(self.event_bus)

        self.logger.debug(f"Registered service: {service.service_name}")

    async def start_service(self, service_name: str) -> None:
        """
        Start a single service.

        Args:
            service_name: Name of the service to start
        """
        if service_name not in self._services:
            raise ValueError(f"Service {service_name} not registered")

        if service_name in self._started_services:
            self.logger.debug(f"Service {service_name} already started")
            return

        # Check dependencies are started
        deps = self.DEPENDENCIES.get(service_name, [])
        for dep in deps:
            if dep not in self._started_services:
                self.logger.error(f"Cannot start {service_name}: dependency {dep} not started")
                raise RuntimeError(f"Dependency {dep} not started for service {service_name}")

        service = self._services[service_name]
        try:
            await service.initialize()
            self._started_services.append(service_name)
            self.logger.info(f"Started service: {service_name}")
        except Exception as e:
            self.logger.error(f"Failed to start {service_name}: {e}")
            raise

    async def start_all_services(self) -> None:
        """Start all registered services in dependency order."""
        self._started_services = []
        self.logger.info("Starting all services...")

        # Determine which services to start
        # Use STARTUP_ORDER for known services, then add any remaining registered services
        services_to_start = []
        for service_name in self.STARTUP_ORDER:
            if service_name in self._services:
                services_to_start.append(service_name)

        # Add any services that aren't in the default order
        for service_name in self._services:
            if service_name not in services_to_start:
                services_to_start.append(service_name)

        # Start services in order
        for service_name in services_to_start:
            try:
                await self.start_service(service_name)
            except RuntimeError:
                raise

        # Publish system started event
        await self.event_bus.publish(
            "system_started", "orchestrator", {"services": self._started_services}
        )
        self.logger.info(f"All services started: {', '.join(self._started_services)}")

    async def start_all(self) -> None:
        """Alias for start_all_services()."""
        await self.start_all_services()

    async def stop_service(self, service_name: str) -> None:
        """
        Stop a single service.

        Args:
            service_name: Name of the service to stop
        """
        if service_name not in self._services:
            raise RuntimeError(f"Service {service_name} not registered")

        if service_name not in self._started_services:
            self.logger.debug(f"Service {service_name} not running")
            return

        service = self._services[service_name]
        try:
            await service.shutdown()
            self._started_services.remove(service_name)
            self.logger.info(f"Stopped service: {service_name}")
        except Exception as e:
            self.logger.error(f"Error stopping {service_name}: {e}")
            raise

    async def stop_all_services(self) -> None:
        """Stop all registered services in reverse dependency order."""
        self.logger.info("Stopping all services...")

        # Determine which services to stop
        # Use reverse STARTUP_ORDER for known services, then add remaining in registration order
        services_to_stop = []
        for service_name in reversed(self.STARTUP_ORDER):
            if service_name in self._services and service_name in self._started_services:
                services_to_stop.append(service_name)

        # Add any services that aren't in the default order
        for service_name in reversed(list(self._services.keys())):
            if service_name not in services_to_stop and service_name in self._started_services:
                services_to_stop.append(service_name)

        for service_name in services_to_stop:
            try:
                await self.stop_service(service_name)
            except RuntimeError:
                pass  # Continue shutdown even if one service fails

        # Publish system stopped event
        await self.event_bus.publish("system_stopped", "orchestrator", {"services": []})
        self.logger.info("All services stopped")

    async def stop_all(self) -> None:
        """Alias for stop_all_services()."""
        await self.stop_all_services()

    async def get_service(self, service_name: str) -> Optional[BaseService]:
        """
        Get a service by name.

        Args:
            service_name: Name of the service to retrieve

        Returns:
            Service instance or None if not found
        """
        return self._services.get(service_name)

    async def call_service(self, service_name: str, method_name: str, *args, **kwargs) -> Any:
        """
        Call a method on a service through the orchestrator.

        This is the standard way services communicate with each other.

        Args:
            service_name: Name of the service to call
            method_name: Name of the method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Result of the method call
        """
        service = self._services.get(service_name)
        if not service:
            raise RuntimeError(f"Service {service_name} not found")

        if service_name not in self._started_services:
            raise RuntimeError(f"Service {service_name} is not running")

        method = getattr(service, method_name, None)
        if not method:
            raise RuntimeError(f"Service {service_name} has no method {method_name}")

        self.logger.debug(f"Calling {service_name}.{method_name}")
        return await method(*args, **kwargs)

    async def health_check_service(self, service_name: str) -> Dict[str, Any]:
        """
        Check health of a single service.

        Args:
            service_name: Name of the service to check

        Returns:
            Dictionary with health status
        """
        if service_name not in self._services:
            raise RuntimeError(f"Service {service_name} not registered")

        service = self._services[service_name]
        is_running = service_name in self._started_services
        try:
            health = await service.health_check()
            # Extract status from health dict if present
            health_status = (
                health.get("status", "healthy") if isinstance(health, dict) else "healthy"
            )
            return {
                "status": health_status,
                "running": is_running,
                "details": health,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "running": False,
                "error": str(e),
            }

    async def health_check(self, service_name: str) -> Dict[str, Any]:
        """Alias for health_check_service()."""
        return await self.health_check_service(service_name)

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Check health of all services.

        Returns:
            Dictionary with health status of each service
        """
        health_status = {}

        for service_name in self._services.keys():
            health_result = await self.health_check_service(service_name)
            health_status[service_name] = health_result

        return health_status

    def get_service_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of a single service or all services.

        Args:
            service_name: Optional name of specific service. If None, returns status of all.

        Returns:
            Dictionary with service status information
        """
        if service_name:
            if service_name not in self._services:
                raise ValueError(f"Service {service_name} not registered")
            service = self._services[service_name]
            return {
                "name": service_name,
                "class": service.__class__.__name__,
                "status": "running" if service_name in self._started_services else "stopped",
            }
        else:
            return {
                service_name: {
                    "class": service.__class__.__name__,
                    "status": "running" if service_name in self._started_services else "stopped",
                }
                for service_name, service in self._services.items()
            }

    def get_all_services_status(self) -> Dict[str, Any]:
        """Alias for get_service_status() to get status of all services."""
        return self.get_service_status()

    def list_services(self) -> Dict[str, str]:
        """List all registered services."""
        return {
            service_name: service.__class__.__name__
            for service_name, service in self._services.items()
        }

    def get_dependencies(self, service_name: str) -> List[str]:
        """Get dependencies for a service."""
        return self.DEPENDENCIES.get(service_name, [])

    async def subscribe_service_to_events(
        self, service_name: str, event_type: str, handler: Callable
    ) -> None:
        """
        Subscribe a service to an event type.

        Args:
            service_name: Name of the service subscribing
            event_type: Type of event to subscribe to
            handler: Async function to handle the event
        """
        self.event_bus.subscribe(event_type, handler)
        self.logger.debug(f"Service {service_name} subscribed to event {event_type}")
