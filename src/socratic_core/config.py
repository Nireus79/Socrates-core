"""
Configuration management for Socratic Core.

Provides configuration classes for initializing services and orchestration.
"""

from pathlib import Path
from typing import Any, Dict, Optional


class SocratesConfig:
    """Configuration for Socrates system."""

    def __init__(
        self,
        api_key: str,
        data_dir: Optional[Path] = None,
        projects_db_path: Optional[Path] = None,
        vector_db_path: Optional[Path] = None,
        embedding_model: str = "claude-3-5-sonnet-20241022",
        claude_model: str = "claude-3-5-sonnet-20241022",
        log_level: str = "INFO",
        debug: bool = False,
        **kwargs: Any,
    ):
        """
        Initialize Socrates configuration.

        Args:
            api_key: API key for LLM providers
            data_dir: Base directory for data storage
            projects_db_path: Path to projects database
            vector_db_path: Path to vector database
            embedding_model: Model to use for embeddings
            claude_model: Claude model identifier for LLM operations
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            debug: Enable debug mode
            **kwargs: Additional configuration options
        """
        self.api_key = api_key
        self.data_dir = data_dir or Path.home() / ".socrates"
        self.projects_db_path = projects_db_path or self.data_dir / "projects.db"
        self.vector_db_path = vector_db_path or self.data_dir / "vector_db"
        self.embedding_model = embedding_model
        self.claude_model = claude_model
        self.log_level = log_level
        self.debug = debug
        self.extra = kwargs

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "api_key": "***" if self.api_key else None,  # Don't expose API key
            "data_dir": str(self.data_dir),
            "projects_db_path": str(self.projects_db_path),
            "vector_db_path": str(self.vector_db_path),
            "embedding_model": self.embedding_model,
            "claude_model": self.claude_model,
            "log_level": self.log_level,
            "debug": self.debug,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SocratesConfig":
        """Create config from dictionary."""
        return SocratesConfig(
            api_key=data.get("api_key", ""),
            data_dir=Path(data["data_dir"]) if "data_dir" in data else None,
            projects_db_path=(
                Path(data["projects_db_path"]) if "projects_db_path" in data else None
            ),
            vector_db_path=(Path(data["vector_db_path"]) if "vector_db_path" in data else None),
            embedding_model=data.get("embedding_model", "claude-3-5-sonnet-20241022"),
            claude_model=data.get("claude_model", "claude-3-5-sonnet-20241022"),
            log_level=data.get("log_level", "INFO"),
            debug=data.get("debug", False),
            **{
                k: v
                for k, v in data.items()
                if k
                not in [
                    "api_key",
                    "data_dir",
                    "projects_db_path",
                    "vector_db_path",
                    "embedding_model",
                    "claude_model",
                    "log_level",
                    "debug",
                ]
            },
        )


class ConfigBuilder:
    """Builder for SocratesConfig."""

    def __init__(self, api_key: str):
        """Initialize builder with API key."""
        self._api_key = api_key
        self._data_dir: Optional[Path] = None
        self._projects_db_path: Optional[Path] = None
        self._vector_db_path: Optional[Path] = None
        self._embedding_model = "claude-3-5-sonnet-20241022"
        self._claude_model = "claude-3-5-sonnet-20241022"
        self._log_level = "INFO"
        self._debug = False
        self._extra: Dict[str, Any] = {}

    def with_data_dir(self, data_dir: Path) -> "ConfigBuilder":
        """Set data directory."""
        self._data_dir = data_dir
        return self

    def with_projects_db(self, path: Path) -> "ConfigBuilder":
        """Set projects database path."""
        self._projects_db_path = path
        return self

    def with_vector_db(self, path: Path) -> "ConfigBuilder":
        """Set vector database path."""
        self._vector_db_path = path
        return self

    def with_embedding_model(self, model: str) -> "ConfigBuilder":
        """Set embedding model."""
        self._embedding_model = model
        return self

    def with_claude_model(self, model: str) -> "ConfigBuilder":
        """Set Claude model."""
        self._claude_model = model
        return self

    def with_log_level(self, level: str) -> "ConfigBuilder":
        """Set log level."""
        self._log_level = level
        return self

    def with_debug(self, debug: bool = True) -> "ConfigBuilder":
        """Enable/disable debug mode."""
        self._debug = debug
        return self

    def with_option(self, key: str, value: Any) -> "ConfigBuilder":
        """Set arbitrary option."""
        self._extra[key] = value
        return self

    def build(self) -> SocratesConfig:
        """Build the configuration."""
        return SocratesConfig(
            api_key=self._api_key,
            data_dir=self._data_dir,
            projects_db_path=self._projects_db_path,
            vector_db_path=self._vector_db_path,
            embedding_model=self._embedding_model,
            claude_model=self._claude_model,
            log_level=self._log_level,
            debug=self._debug,
            **self._extra,
        )
