"""
Event system for Socratic Core.

Provides event emission and handling capabilities.
"""

from enum import Enum
from typing import Any, Callable, Dict, List


class EventType(str, Enum):
    """Complete event type enumeration - 97+ event types across all domains."""

    # ==================== WORKFLOW EVENTS (12) ====================
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_CHANGED = "phase_changed"
    PHASE_GATING_CHECK = "phase_gating_check"
    PHASE_GATE_PASSED = "phase_gate_passed"
    PHASE_GATE_FAILED = "phase_gate_failed"

    # ==================== AGENT EVENTS (15) ====================
    AGENT_INITIALIZED = "agent_initialized"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_TIMEOUT = "agent_timeout"
    AGENT_QUEUED = "agent_queued"
    AGENT_EXECUTING = "agent_executing"
    AGENT_CACHED = "agent_cached"
    AGENT_CACHE_HIT = "agent_cache_hit"
    AGENT_CACHE_MISS = "agent_cache_miss"
    AGENT_ERROR = "agent_error"
    AGENT_RETRY = "agent_retry"
    AGENT_SKIPPED = "agent_skipped"
    AGENT_DEPRECATED = "agent_deprecated"
    AGENT_UPDATED = "agent_updated"

    # ==================== SKILL EVENTS (14) ====================
    SKILL_GENERATED = "skill_generated"
    SKILL_VALIDATED = "skill_validated"
    SKILL_APPLIED = "skill_applied"
    SKILL_FAILED = "skill_failed"
    SKILL_COMPOSED = "skill_composed"
    SKILL_VERSIONED = "skill_versioned"
    SKILL_DEPRECATED = "skill_deprecated"
    SKILL_COMPATIBILITY_CHECK = "skill_compatibility_check"
    SKILL_PARAMETER_OPTIMIZED = "skill_parameter_optimized"
    SKILL_EFFECTIVENESS_ANALYZED = "skill_effectiveness_analyzed"
    SKILL_RECOMMENDATION_GENERATED = "skill_recommendation_generated"
    SKILL_ORCHESTRATION_STARTED = "skill_orchestration_started"
    SKILL_ORCHESTRATION_COMPLETED = "skill_orchestration_completed"
    SKILL_INTERACTION_TRACKED = "skill_interaction_tracked"

    # ==================== QUALITY & VALIDATION EVENTS (11) ====================
    QUALITY_GATE_PASSED = "quality_gate_passed"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    CODE_REVIEWED = "code_reviewed"
    CODE_VALIDATED = "code_validated"
    DESIGN_VALIDATED = "design_validated"
    ARCHITECTURE_VALIDATED = "architecture_validated"
    PERFORMANCE_VALIDATED = "performance_validated"
    SECURITY_VALIDATED = "security_validated"
    TEST_COVERAGE_ANALYZED = "test_coverage_analyzed"
    VALIDATION_STARTED = "validation_started"
    VALIDATION_COMPLETED = "validation_completed"

    # ==================== LEARNING & FEEDBACK EVENTS (12) ====================
    LEARNING_STARTED = "learning_started"
    LEARNING_COMPLETED = "learning_completed"
    FEEDBACK_RECORDED = "feedback_recorded"
    FEEDBACK_ANALYZED = "feedback_analyzed"
    PATTERN_DETECTED = "pattern_detected"
    BEHAVIOR_ANALYZED = "behavior_analyzed"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    EFFECTIVENESS_CALCULATED = "effectiveness_calculated"
    USER_INTERACTION = "user_interaction"
    QUESTION_ANSWERED = "question_answered"
    LEARNING_GOAL_ACHIEVED = "learning_goal_achieved"
    MATURITY_UPDATED = "maturity_updated"

    # ==================== CONFLICT RESOLUTION EVENTS (8) ====================
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_ANALYZED = "conflict_analyzed"
    CONFLICT_RESOLVED = "conflict_resolved"
    CONFLICT_ESCALATED = "conflict_escalated"
    CONSENSUS_REACHED = "consensus_reached"
    CONSENSUS_FAILED = "consensus_failed"
    DECISION_MADE = "decision_made"
    RESOLUTION_APPROVED = "resolution_approved"

    # ==================== KNOWLEDGE & CONTEXT EVENTS (11) ====================
    KNOWLEDGE_INDEXED = "knowledge_indexed"
    KNOWLEDGE_RETRIEVED = "knowledge_retrieved"
    KNOWLEDGE_UPDATED = "knowledge_updated"
    KNOWLEDGE_DELETED = "knowledge_deleted"
    KNOWLEDGE_SUGGESTION = "knowledge_suggestion"
    CONTEXT_ANALYZED = "context_analyzed"
    CONTEXT_ENRICHED = "context_enriched"
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_ANALYZED = "document_analyzed"
    SEMANTIC_SEARCH_PERFORMED = "semantic_search_performed"
    KNOWLEDGE_GRAPH_UPDATED = "knowledge_graph_updated"

    # ==================== PERFORMANCE & MONITORING EVENTS (11) ====================
    PERFORMANCE_METRIC_RECORDED = "performance_metric_recorded"
    LATENCY_THRESHOLD_EXCEEDED = "latency_threshold_exceeded"
    TOKEN_LIMIT_APPROACHING = "token_limit_approaching"
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"
    COST_THRESHOLD_EXCEEDED = "cost_threshold_exceeded"
    RESOURCE_USAGE_HIGH = "resource_usage_high"
    HEALTH_CHECK_PASSED = "health_check_passed"
    HEALTH_CHECK_FAILED = "health_check_failed"
    BOTTLENECK_DETECTED = "bottleneck_detected"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"
    MONITORING_ALERT = "monitoring_alert"

    # ==================== DATA & PERSISTENCE EVENTS (8) ====================
    DATA_CREATED = "data_created"
    DATA_SAVED = "data_saved"
    DATA_LOADED = "data_loaded"
    DATA_UPDATED = "data_updated"
    DATA_VALIDATED = "data_validated"
    DATA_TRANSFORMED = "data_transformed"
    DATA_DELETED = "data_deleted"
    DATABASE_ERROR = "database_error"

    # ==================== USER & SESSION EVENTS (7) ====================
    USER_AUTHENTICATED = "user_authenticated"
    USER_SESSION_STARTED = "user_session_started"
    USER_SESSION_ENDED = "user_session_ended"
    USER_PREFERENCE_CHANGED = "user_preference_changed"
    USER_ROLE_CHANGED = "user_role_changed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"

    # ==================== ERROR & RECOVERY EVENTS (6) ====================
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_ERROR = "system_error"
    SERVICE_ERROR = "service_error"
    ERROR_RECOVERED = "error_recovered"
    FATAL_ERROR = "fatal_error"
    RETRY_SCHEDULED = "retry_scheduled"

    # ==================== COORDINATION EVENTS (3) ====================
    WORKFLOW_COORDINATION = "workflow_coordination"
    MULTI_AGENT_SYNC = "multi_agent_sync"
    ORCHESTRATION_COMPLETE = "orchestration_complete"

    # ==================== LOGGING EVENTS (4) ====================
    LOG_DEBUG = "log_debug"
    LOG_INFO = "log_info"
    LOG_WARNING = "log_warning"
    LOG_ERROR = "log_error"


class EventEmitter:
    """Simple event emitter for decoupled communication."""

    def __init__(self):
        """Initialize event emitter."""
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, listener: Callable) -> None:
        """
        Register a listener for an event.

        Args:
            event: Event name
            listener: Callable to invoke when event occurs
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)

    def off(self, event: str, listener: Callable) -> None:
        """
        Unregister a listener for an event.

        Args:
            event: Event name
            listener: Callable to remove
        """
        if event in self._listeners:
            self._listeners[event].remove(listener)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        Emit an event to all registered listeners.

        Args:
            event: Event name
            *args: Positional arguments for listeners
            **kwargs: Keyword arguments for listeners
        """
        if event in self._listeners:
            for listener in self._listeners[event]:
                try:
                    listener(*args, **kwargs)
                except Exception as e:
                    # Log error but don't fail
                    print(f"Error in event listener for {event}: {e}")

    def once(self, event: str, listener: Callable) -> None:
        """
        Register a one-time listener for an event.

        Args:
            event: Event name
            listener: Callable to invoke once when event occurs
        """

        def one_time_listener(*args: Any, **kwargs: Any) -> None:
            listener(*args, **kwargs)
            self.off(event, one_time_listener)

        self.on(event, one_time_listener)
