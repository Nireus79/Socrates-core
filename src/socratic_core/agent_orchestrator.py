"""
Agent Orchestrator - Coordinates multi-agent workflows for modular Socrates.

Provides:
- Agent registration and discovery
- Request routing to agents
- Event emission for inter-agent communication
- Agent caching and lazy initialization
- Cross-library agent coordination
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Central orchestrator for coordinating agents across modular libraries.

    Handles agent registration, routing, event emission, and lifecycle management.
    Agents from different libraries (socratic-agents, socratic-rag, etc.) can be
    registered and coordinated through this orchestrator.
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        database: Optional[Any] = None,
    ):
        """
        Initialize the agent orchestrator.

        Args:
            config: Optional SocratesConfig for configuration
            event_bus: Optional EventBus for inter-agent communication
            database: Optional DatabaseClient for persistence
        """
        self.config = config
        self.event_bus = event_bus
        self.database = database
        self.logger = logging.getLogger(f"{__name__}.AgentOrchestrator")

        # Agent registry: name -> agent instance
        self._agents: Dict[str, Any] = {}

        # Agent metadata for discovery
        self._agent_metadata: Dict[str, Dict[str, Any]] = {}

        # Lazy-loaded agents for performance
        self._lazy_agents: Dict[str, Any] = {}

        self.logger.info("AgentOrchestrator initialized")

    def register_agent(
        self,
        name: str,
        agent: Any,
        description: str = "",
        capabilities: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register an agent with the orchestrator.

        Args:
            name: Unique agent name
            agent: Agent instance
            description: Human-readable description
            capabilities: List of agent capabilities
            metadata: Additional metadata dict
        """
        self._agents[name] = agent

        self._agent_metadata[name] = {
            "description": description,
            "capabilities": capabilities or [],
            "metadata": metadata or {},
        }

        self.logger.info(f"Registered agent: {name}")

        # Emit registration event if event bus available
        if self.event_bus:
            self.event_bus.emit(
                "agent_registered", {"agent_name": name, "description": description}
            )

    def register_lazy_agent(
        self,
        name: str,
        factory: callable,
        description: str = "",
        capabilities: Optional[list] = None,
    ) -> None:
        """
        Register a lazy-loaded agent (created on first use).

        Args:
            name: Unique agent name
            factory: Callable that returns agent instance
            description: Human-readable description
            capabilities: List of agent capabilities
        """
        self._lazy_agents[name] = factory

        self._agent_metadata[name] = {
            "description": description,
            "capabilities": capabilities or [],
            "lazy": True,
        }

        self.logger.info(f"Registered lazy agent: {name}")

    def get_agent(self, name: str) -> Optional[Any]:
        """
        Get agent by name (lazy-loads if needed).

        Args:
            name: Agent name

        Returns:
            Agent instance or None if not found
        """
        # Check directly registered agents first
        if name in self._agents:
            return self._agents[name]

        # Check lazy agents
        if name in self._lazy_agents:
            factory = self._lazy_agents[name]
            agent = factory()
            self._agents[name] = agent  # Cache after creation
            del self._lazy_agents[name]  # Remove from lazy dict
            return agent

        return None

    def call_agent(
        self,
        agent_name: str,
        request: Dict[str, Any],
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Call an agent with a request.

        Args:
            agent_name: Name of agent to call
            request: Request dict
            timeout: Optional timeout in seconds

        Returns:
            Response dict from agent
        """
        agent = self.get_agent(agent_name)
        if not agent:
            return {
                "status": "error",
                "message": f"Agent not found: {agent_name}",
            }

        try:
            # Emit pre-request event
            if self.event_bus:
                self.event_bus.emit(
                    "agent_request_start", {"agent": agent_name, "request": request}
                )

            # Call agent's process method
            if hasattr(agent, "process"):
                result = agent.process(request)
            elif callable(agent):
                result = agent(request)
            else:
                result = {
                    "status": "error",
                    "message": f"Agent {agent_name} is not callable",
                }

            # Emit post-request event
            if self.event_bus:
                self.event_bus.emit(
                    "agent_request_complete", {"agent": agent_name, "result": result}
                )

            return result

        except Exception as e:
            self.logger.error(f"Error calling agent {agent_name}: {str(e)}")

            # Emit error event
            if self.event_bus:
                self.event_bus.emit("agent_error", {"agent": agent_name, "error": str(e)})

            return {
                "status": "error",
                "message": f"Agent error: {str(e)}",
            }

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered agents with metadata.

        Returns:
            Dict of agent names -> metadata
        """
        return {name: self._agent_metadata.get(name, {}) for name in self._agents.keys()}

    def get_agents_by_capability(self, capability: str) -> list:
        """
        Find all agents with a specific capability.

        Args:
            capability: Capability name

        Returns:
            List of agent names
        """
        matching = []
        for name, metadata in self._agent_metadata.items():
            if capability in metadata.get("capabilities", []):
                matching.append(name)
        return matching

    def workflow(self, steps: list) -> Dict[str, Any]:
        """
        Execute a workflow (sequence of agent calls).

        Args:
            steps: List of dicts with format:
                {
                    "agent": "agent_name",
                    "request": {...},
                    "save_as": "variable_name"  # optional
                }

        Returns:
            Workflow result with all step outputs
        """
        workflow_results = {}
        variables = {}

        try:
            for step_idx, step in enumerate(steps):
                agent_name = step.get("agent")
                request = step.get("request", {})
                save_as = step.get("save_as")

                if not agent_name:
                    self.logger.error(f"Step {step_idx} missing agent name")
                    continue

                # Substitute variables in request
                request = self._substitute_variables(request, variables)

                # Call agent
                result = self.call_agent(agent_name, request)
                workflow_results[f"step_{step_idx}"] = result

                # Save output if requested
                if save_as:
                    variables[save_as] = result

            return {
                "status": "success",
                "steps_completed": len(steps),
                "results": workflow_results,
            }

        except Exception as e:
            self.logger.error(f"Workflow execution error: {str(e)}")
            return {
                "status": "error",
                "message": f"Workflow error: {str(e)}",
                "results": workflow_results,
            }

    def _substitute_variables(self, obj: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute ${var} references in object."""
        if isinstance(obj, dict):
            return {k: self._substitute_variables(v, variables) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_variables(item, variables) for item in obj]
        elif isinstance(obj, str):
            # Replace ${var} with variable value
            for var_name, var_value in variables.items():
                obj = obj.replace(f"${{{var_name}}}", str(var_value))
            return obj
        return obj

    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Emit an event through the event bus.

        Args:
            event_type: Event type name
            data: Event data dict
        """
        if self.event_bus:
            self.event_bus.emit(event_type, data)
        else:
            self.logger.debug(f"Event emitted (no event bus): {event_type}")

    def on_event(self, event_type: str, callback: callable) -> None:
        """
        Register event listener.

        Args:
            event_type: Event type to listen for
            callback: Callback function
        """
        if self.event_bus:
            self.event_bus.on(event_type, callback)

    def shutdown(self) -> None:
        """Shutdown orchestrator and cleanup agents."""
        self.logger.info("Shutting down agent orchestrator...")

        # Emit shutdown event
        self.emit_event("system_shutdown", {})

        # Clear agent caches
        self._agents.clear()
        self._lazy_agents.clear()

        self.logger.info("Agent orchestrator shutdown complete")
