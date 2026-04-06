"""
SharedModels - Common data models used across all services.

Pydantic v2 models for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class InteractionStatus(str, Enum):
    """Status of an interaction."""

    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SkillType(str, Enum):
    """Type of skill."""

    ANALYSIS = "analysis"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    LEARNING = "learning"
    CONFLICT_RESOLUTION = "conflict_resolution"


class WorkflowStatus(str, Enum):
    """Status of a workflow."""

    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Interaction(BaseModel):
    """Record of an agent interaction."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "interaction_id": "int_12345",
                "agent_name": "AnalysisAgent",
                "agent_type": "analysis",
                "status": "completed",
                "input_data": {"query": "Analyze code"},
                "output_data": {"result": "Analysis complete"},
                "metrics": {"tokens_used": 150},
                "timestamp": "2026-03-16T12:34:56",
                "duration_ms": 1234.5,
            }
        }
    )

    interaction_id: str = Field(..., description="Unique interaction ID")
    agent_name: str = Field(..., description="Name of agent that performed action")
    agent_type: str = Field(..., description="Type of agent")
    status: InteractionStatus = Field(default=InteractionStatus.IN_PROGRESS)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None


class Skill(BaseModel):
    """A skill that an agent has learned."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skill_id": "skill_789",
                "agent_name": "AnalysisAgent",
                "skill_name": "deep_code_analysis",
                "skill_type": "analysis",
                "description": "Analyze code for patterns and issues",
                "effectiveness": 0.92,
                "usage_count": 42,
                "success_rate": 0.88,
                "created_at": "2026-03-16T10:00:00",
            }
        }
    )

    skill_id: str = Field(..., description="Unique skill ID")
    agent_name: str = Field(..., description="Agent this skill belongs to")
    skill_name: str = Field(..., description="Name of the skill")
    skill_type: SkillType = Field(...)
    description: str = Field(..., description="What this skill does")
    effectiveness: float = Field(default=0.0, ge=0.0, le=1.0, description="0-1 score")
    usage_count: int = Field(default=0, description="Times this skill has been used")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None


class Metric(BaseModel):
    """Performance metric."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metric_name": "api_latency_ms",
                "metric_type": "histogram",
                "value": 123.45,
                "timestamp": "2026-03-16T12:34:56",
                "service_name": "agents",
                "tags": {"endpoint": "/execute", "agent": "AnalysisAgent"},
            }
        }
    )

    metric_name: str = Field(..., description="Name of metric")
    metric_type: str = Field(..., description="Type: counter, gauge, histogram")
    value: float = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service_name: str = Field(..., description="Service that produced this metric")
    tags: Dict[str, str] = Field(default_factory=dict)


class Recommendation(BaseModel):
    """A recommendation for agent improvement."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommendation_id": "rec_123",
                "agent_name": "AnalysisAgent",
                "recommendation_type": "skill_generation",
                "title": "Learn pattern detection",
                "description": "Agent frequently encounters similar patterns",
                "priority": 3,
                "confidence": 0.87,
                "suggested_action": "Generate skill for pattern detection",
                "created_at": "2026-03-16T12:34:56",
            }
        }
    )

    recommendation_id: str = Field(...)
    agent_name: str = Field(...)
    recommendation_type: str = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    priority: int = Field(ge=1, le=5, description="1=low, 5=critical")
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_action: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TimestampedModel(BaseModel):
    """Base model with timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IdentifiedModel(BaseModel):
    """Base model with ID field."""

    id: str = Field(..., description="Unique identifier")


class User(BaseModel):
    """User representation across all Socratic services."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "usr_12345",
                "username": "john_doe",
                "email": "john@example.com",
                "subscription_tier": "pro",
                "created_at": "2026-03-16T10:00:00",
                "updated_at": "2026-03-16T12:00:00",
            }
        }
    )

    user_id: str = Field(..., description="Unique user ID")
    username: str = Field(..., description="Unique username")
    email: Optional[str] = Field(None, description="User email")
    subscription_tier: str = Field(default="free", description="free, pro, enterprise")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Project(BaseModel):
    """Project representation across all Socratic services."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "proj_12345",
                "user_id": "usr_12345",
                "name": "E-Commerce Platform",
                "phase": "discovery",
                "description": "Building an e-commerce platform",
                "created_at": "2026-03-16T10:00:00",
                "updated_at": "2026-03-16T12:00:00",
            }
        }
    )

    project_id: str = Field(..., description="Unique project ID")
    user_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="Project name")
    phase: str = Field(default="discovery", description="discovery, analysis, design, implementation")
    description: Optional[str] = Field(None, description="Project description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    """Session representation across all Socratic services."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "sess_12345",
                "user_id": "usr_12345",
                "project_id": "proj_12345",
                "started_at": "2026-03-16T10:00:00",
                "ended_at": "2026-03-16T12:00:00",
            }
        }
    )

    session_id: str = Field(..., description="Unique session ID")
    user_id: str = Field(..., description="User ID")
    project_id: Optional[str] = Field(None, description="Project ID if session is project-specific")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Question(BaseModel):
    """Question representation for Socratic Counselor."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "q_12345",
                "project_id": "proj_12345",
                "phase": "discovery",
                "question": "What are the main requirements for your system?",
                "status": "unanswered",
                "answer": None,
                "created_at": "2026-03-16T10:00:00",
            }
        }
    )

    question_id: str = Field(..., description="Unique question ID")
    project_id: str = Field(..., description="Project ID")
    phase: str = Field(..., description="Phase this question belongs to")
    question: str = Field(..., description="The question text")
    status: str = Field(default="unanswered", description="unanswered, answered, skipped")
    answer: Optional[str] = Field(None, description="User's answer")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    answered_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
