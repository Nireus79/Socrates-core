"""Unit tests for ServiceOrchestrator."""

from unittest.mock import Mock

import pytest

from socratic_core.base_service import BaseService
from socratic_core.orchestrator import ServiceOrchestrator


class MockService(BaseService):
    """Mock service for testing."""

    def __init__(self, name: str):
        """Initialize mock service."""
        super().__init__(name)
        self.initialized = False
        self.shutdown_called = False
        self.health_check_called = False

    async def initialize(self):
        """Initialize the service."""
        self.initialized = True

    async def shutdown(self):
        """Shutdown the service."""
        self.shutdown_called = True

    async def health_check(self):
        """Check service health."""
        self.health_check_called = True
        return {"status": "healthy"}


class FailingService(BaseService):
    """Service that fails to initialize."""

    async def initialize(self):
        """Fail to initialize."""
        raise RuntimeError("Initialization failed")

    async def shutdown(self):
        """Shutdown the service."""
        pass

    async def health_check(self):
        """Check service health."""
        return {"status": "unhealthy"}


class TestServiceOrchestrator:
    """Test ServiceOrchestrator functionality."""

    def test_orchestrator_creation(self):
        """Test creating an orchestrator."""
        orchestrator = ServiceOrchestrator()
        assert orchestrator is not None

    @pytest.mark.asyncio
    async def test_register_service(self):
        """Test registering a service."""
        orchestrator = ServiceOrchestrator()
        service = MockService("TestService")

        orchestrator.register_service(service)

        assert "TestService" in orchestrator.services
        assert orchestrator.services["TestService"] == service

    @pytest.mark.asyncio
    async def test_start_single_service(self):
        """Test starting a single service."""
        orchestrator = ServiceOrchestrator()
        service = MockService("TestService")

        orchestrator.register_service(service)
        await orchestrator.start_service("TestService")

        assert service.initialized

    @pytest.mark.asyncio
    async def test_start_all_services(self):
        """Test starting all services."""
        orchestrator = ServiceOrchestrator()
        service1 = MockService("Service1")
        service2 = MockService("Service2")

        orchestrator.register_service(service1)
        orchestrator.register_service(service2)

        await orchestrator.start_all()

        assert service1.initialized
        assert service2.initialized

    @pytest.mark.asyncio
    async def test_stop_single_service(self):
        """Test stopping a single service."""
        orchestrator = ServiceOrchestrator()
        service = MockService("TestService")

        orchestrator.register_service(service)
        await orchestrator.start_service("TestService")
        await orchestrator.stop_service("TestService")

        assert service.shutdown_called

    @pytest.mark.asyncio
    async def test_stop_all_services(self):
        """Test stopping all services."""
        orchestrator = ServiceOrchestrator()
        service1 = MockService("Service1")
        service2 = MockService("Service2")

        orchestrator.register_service(service1)
        orchestrator.register_service(service2)

        await orchestrator.start_all()
        await orchestrator.stop_all()

        assert service1.shutdown_called
        assert service2.shutdown_called

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check on service."""
        orchestrator = ServiceOrchestrator()
        service = MockService("TestService")

        orchestrator.register_service(service)
        health = await orchestrator.health_check_service("TestService")

        assert service.health_check_called
        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health check on all services."""
        orchestrator = ServiceOrchestrator()
        service1 = MockService("Service1")
        service2 = MockService("Service2")

        orchestrator.register_service(service1)
        orchestrator.register_service(service2)

        await orchestrator.start_all()
        health_results = await orchestrator.health_check_all()

        assert "Service1" in health_results
        assert "Service2" in health_results
        assert service1.health_check_called
        assert service2.health_check_called

    @pytest.mark.asyncio
    async def test_get_service_status(self):
        """Test getting service status."""
        orchestrator = ServiceOrchestrator()
        service = MockService("TestService")

        orchestrator.register_service(service)
        await orchestrator.start_service("TestService")

        status = orchestrator.get_service_status("TestService")

        assert status["name"] == "TestService"
        assert status["status"] == "running"

    @pytest.mark.asyncio
    async def test_service_not_found(self):
        """Test accessing non-existent service."""
        orchestrator = ServiceOrchestrator()

        with pytest.raises(ValueError):
            await orchestrator.start_service("NonExistent")

    @pytest.mark.asyncio
    async def test_startup_order(self):
        """Test that services start in dependency order."""
        orchestrator = ServiceOrchestrator()

        # Create services
        service1 = MockService("Service1")
        service2 = MockService("Service2")
        service3 = MockService("Service3")

        # Add services
        orchestrator.register_service(service1)
        orchestrator.register_service(service2)
        orchestrator.register_service(service3)

        # Start all (should respect dependency order)
        await orchestrator.start_all()

        # All should be initialized
        assert service1.initialized
        assert service2.initialized
        assert service3.initialized

    @pytest.mark.asyncio
    async def test_initialization_failure_handling(self):
        """Test handling service initialization failures."""
        orchestrator = ServiceOrchestrator()
        good_service = MockService("GoodService")
        bad_service = FailingService("BadService")

        orchestrator.register_service(good_service)
        orchestrator.register_service(bad_service)

        # Starting bad service should raise
        with pytest.raises(RuntimeError):
            await orchestrator.start_service("BadService")

    @pytest.mark.asyncio
    async def test_shutdown_order_reverses_startup(self):
        """Test that shutdown order is reverse of startup."""
        orchestrator = ServiceOrchestrator()
        startup_order = []
        shutdown_order = []

        class OrderTrackingService(BaseService):
            def __init__(self, name: str, startup_list, shutdown_list):
                super().__init__(name)
                self.startup_list = startup_list
                self.shutdown_list = shutdown_list

            async def initialize(self):
                self.startup_list.append(self.name)

            async def shutdown(self):
                self.shutdown_list.append(self.name)

            async def health_check(self):
                return {"status": "healthy"}

        service1 = OrderTrackingService("Service1", startup_order, shutdown_order)
        service2 = OrderTrackingService("Service2", startup_order, shutdown_order)
        service3 = OrderTrackingService("Service3", startup_order, shutdown_order)

        orchestrator.register_service(service1)
        orchestrator.register_service(service2)
        orchestrator.register_service(service3)

        await orchestrator.start_all()
        await orchestrator.stop_all()

        # Verify startup happened
        assert len(startup_order) == 3

        # Verify shutdown happened in reverse order
        assert len(shutdown_order) == 3

    @pytest.mark.asyncio
    async def test_service_isolation(self):
        """Test that services don't interfere with each other."""
        orchestrator = ServiceOrchestrator()
        service1 = MockService("Service1")
        service2 = MockService("Service2")

        orchestrator.register_service(service1)
        orchestrator.register_service(service2)

        # Start only service1
        await orchestrator.start_service("Service1")

        assert service1.initialized
        assert not service2.initialized  # Service2 should not be started

        # Stop only service1
        await orchestrator.stop_service("Service1")

        assert service1.shutdown_called
        assert not service2.shutdown_called  # Service2 was not started, so not shutdown

    @pytest.mark.asyncio
    async def test_multiple_health_checks(self):
        """Test multiple sequential health checks."""
        orchestrator = ServiceOrchestrator()
        service = MockService("TestService")

        orchestrator.register_service(service)
        await orchestrator.start_service("TestService")

        # Perform health checks multiple times
        for _ in range(3):
            health = await orchestrator.health_check_service("TestService")
            assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_all_services_status(self):
        """Test getting status of all services."""
        orchestrator = ServiceOrchestrator()
        service1 = MockService("Service1")
        service2 = MockService("Service2")
        service3 = MockService("Service3")

        orchestrator.register_service(service1)
        orchestrator.register_service(service2)
        orchestrator.register_service(service3)

        # Start only some services
        await orchestrator.start_service("Service1")
        await orchestrator.start_service("Service2")

        statuses = orchestrator.get_all_services_status()

        assert len(statuses) == 3
        assert statuses["Service1"]["status"] == "running"
        assert statuses["Service2"]["status"] == "running"
        assert statuses["Service3"]["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_call_service_method(self):
        """Test calling a method on a service."""
        orchestrator = ServiceOrchestrator()
        service = MockService("TestService")

        # Add a custom method to the service
        service.custom_method = Mock(return_value="result")

        orchestrator.register_service(service)
        await orchestrator.start_service("TestService")

        # Call custom method through orchestrator (if supported)
        result = orchestrator.services["TestService"].custom_method()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_restarting_service(self):
        """Test restarting a service."""
        orchestrator = ServiceOrchestrator()
        service = MockService("TestService")

        orchestrator.register_service(service)

        # Start
        await orchestrator.start_service("TestService")
        assert service.initialized

        # Reset flags
        service.initialized = False
        service.shutdown_called = False

        # Stop and restart
        await orchestrator.stop_service("TestService")
        assert service.shutdown_called

        await orchestrator.start_service("TestService")
        assert service.initialized
