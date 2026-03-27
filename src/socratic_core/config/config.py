"""
Socrates Configuration System

Supports three initialization methods:
1. From environment variables
2. From dictionary
3. Using ConfigBuilder (fluent API)

Examples:
    >>> config = SocratesConfig.from_env()
    >>> config = SocratesConfig.from_dict({"api_key": "sk-...", "data_dir": "/path"})
    >>> config = ConfigBuilder("sk-...").with_data_dir("/path").build()
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class SocratesConfig:
    """
    Socrates configuration with sensible defaults and flexible customization.

    Supports multiple LLM providers via socrates-nexus:
    - Anthropic (Claude)
    - OpenAI (GPT)
    - Google (Gemini)
    - Ollama (local models)

    Attributes:
        provider: LLM provider (anthropic, openai, google, ollama)
        api_key: LLM API key (optional for API server mode)
        model: Model identifier for the selected provider
        data_dir: Directory for storing projects and databases
        projects_db_path: Path to projects database
        vector_db_path: Path to vector database
        embedding_model: Model for generating embeddings
        max_context_length: Maximum context length for prompts
        max_retries: Maximum number of API retries
        retry_delay: Delay between retries in seconds
        token_warning_threshold: Threshold for token usage warnings (0-1)
        session_timeout: Session timeout in seconds
        log_level: Logging level
        log_file: Path to log file (None = no file logging)
        custom_knowledge: List of custom knowledge entries
    """

    # Provider Configuration
    provider: str = "anthropic"  # anthropic, openai, google, ollama
    api_key: Optional[str] = None  # LLM API key (optional for API server mode)

    # Model Configuration
    model: str = "claude-haiku-4-5-20251001"  # Provider-specific model identifier
    embedding_model: str = "all-MiniLM-L6-v2"

    # Storage Configuration
    data_dir: Path = field(default_factory=lambda: Path.home() / ".socrates")
    projects_db_path: Optional[Path] = None
    vector_db_path: Optional[Path] = None

    # Behavior Configuration
    max_context_length: int = 8000
    max_retries: int = 3
    retry_delay: float = 1.0
    token_warning_threshold: float = 0.8
    session_timeout: int = 3600

    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    # Custom Knowledge
    custom_knowledge: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize derived paths and create directories"""
        self._validate_api_key()
        self._ensure_data_dir_is_path()
        self._initialize_derived_paths()
        self._validate_all_paths()
        self._create_directories()

    def _validate_api_key(self) -> None:
        """
        Validate API key configuration.

        For Ollama provider, API key is optional (local). For other providers, it's required.

        Raises:
            ValueError: If API key is required but missing
        """
        # Ollama doesn't require API key (local provider)
        if self.provider == "ollama":
            return

        # Other providers require API key
        if self.api_key is None or (isinstance(self.api_key, str) and not self.api_key.strip()):
            raise ValueError(
                f"API key is required for provider '{self.provider}'. "
                f"Set LLM_API_KEY or provider-specific key environment variable"
            )

    def _ensure_data_dir_is_path(self) -> None:
        """Ensure data_dir is a Path object"""
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        elif not isinstance(self.data_dir, Path):
            raise TypeError(f"data_dir must be str or Path, got {type(self.data_dir)}")

    def _initialize_derived_paths(self) -> None:
        """Initialize derived paths if not explicitly set"""
        if self.projects_db_path is None:
            self.projects_db_path = self.data_dir / "projects.db"
        elif isinstance(self.projects_db_path, str):
            self.projects_db_path = Path(self.projects_db_path)

        if self.vector_db_path is None:
            self.vector_db_path = self.data_dir / "vector_db"
        elif isinstance(self.vector_db_path, str):
            self.vector_db_path = Path(self.vector_db_path)

        if self.log_file is None:
            self.log_file = self.data_dir / "logs" / "socrates.log"
        elif isinstance(self.log_file, str):
            self.log_file = Path(self.log_file)

    def _validate_all_paths(self) -> None:
        """Validate all paths are now Path objects"""
        if not isinstance(self.projects_db_path, Path):
            raise TypeError(f"projects_db_path must be Path, got {type(self.projects_db_path)}")
        if not isinstance(self.vector_db_path, Path):
            raise TypeError(f"vector_db_path must be Path, got {type(self.vector_db_path)}")
        if not isinstance(self.log_file, Path):
            raise TypeError(f"log_file must be Path, got {type(self.log_file)}")

    def _create_directories(self) -> None:
        """Create required directories"""
        if not isinstance(self.data_dir, Path):
            raise TypeError(f"data_dir must be a Path object, got {type(self.data_dir)}")

        self.data_dir.mkdir(parents=True, exist_ok=True)

        if self.vector_db_path and isinstance(self.vector_db_path, Path):
            self.vector_db_path.mkdir(parents=True, exist_ok=True)

        if self.log_file and isinstance(self.log_file, Path):
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls, **overrides) -> "SocratesConfig":
        """
        Create configuration from environment variables.

        Supports multiple LLM providers:
        - Anthropic: ANTHROPIC_API_KEY, CLAUDE_MODEL
        - OpenAI: OPENAI_API_KEY, OPENAI_MODEL
        - Google: GOOGLE_API_KEY, GOOGLE_MODEL
        - Ollama: OLLAMA_BASE_URL, OLLAMA_MODEL (no API key needed)

        Environment variables:
            LLM_PROVIDER: Provider name (anthropic, openai, google, ollama)
            LLM_API_KEY: Generic LLM API key
            LLM_MODEL: Generic model identifier
            ANTHROPIC_API_KEY: Anthropic-specific key
            OPENAI_API_KEY: OpenAI-specific key
            GOOGLE_API_KEY: Google-specific key
            SOCRATES_DATA_DIR: Data directory
            SOCRATES_LOG_LEVEL: Logging level
            SOCRATES_LOG_FILE: Log file path

        Args:
            **overrides: Override specific settings

        Returns:
            Configured SocratesConfig instance
        """
        # Determine provider
        provider: str = (
            overrides.get("provider") or os.getenv("LLM_PROVIDER", "anthropic") or "anthropic"
        )

        # Get API key from generic or provider-specific env vars
        api_key = (
            overrides.get("api_key")
            or os.getenv("LLM_API_KEY")
            or os.getenv(f"{provider.upper()}_API_KEY")
        )

        # Get model from generic or provider-specific env vars
        model = (
            overrides.get("model")
            or os.getenv("LLM_MODEL")
            or os.getenv(f"{provider.upper()}_MODEL")
        )

        # Set provider-specific defaults if no model specified
        if not model:
            if provider == "anthropic":
                model = "claude-haiku-4-5-20251001"
            elif provider == "openai":
                model = "gpt-4o-mini"
            elif provider == "google":
                model = "gemini-2.0-flash"
            elif provider == "ollama":
                model = "llama2"
            else:
                model = "gpt-4o-mini"  # Safe default

        config_dict = {
            "provider": provider,
            "api_key": api_key,
            "model": model,
            "data_dir": (
                overrides.get("data_dir")
                or Path(os.getenv("SOCRATES_DATA_DIR", Path.home() / ".socrates"))
            ),
            "log_level": (overrides.get("log_level") or os.getenv("SOCRATES_LOG_LEVEL", "INFO")),
        }

        log_file = overrides.get("log_file") or os.getenv("SOCRATES_LOG_FILE")
        if log_file:
            config_dict["log_file"] = Path(log_file)

        config_dict.update(overrides)
        return cls(**config_dict)  # type: ignore[arg-type]

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SocratesConfig":
        """
        Create configuration from a dictionary.

        Args:
            config_dict: Dictionary with configuration values
                Must include: provider, model
                Must include api_key (except for ollama provider)

        Returns:
            Configured SocratesConfig instance

        Raises:
            ValueError: If required fields are missing
        """
        # Make a copy to avoid modifying the original
        config = dict(config_dict)

        # Validate required fields
        if "model" not in config:
            raise ValueError("model is required in configuration")

        provider = config.get("provider", "anthropic")
        if provider != "ollama" and "api_key" not in config:
            raise ValueError(
                f"api_key is required for provider '{provider}'. "
                f"Ollama is the only provider that doesn't require an API key"
            )

        return cls(**config)

    def get_legacy_config_dict(self) -> Dict[str, Any]:
        """
        Get configuration in legacy dictionary format for backward compatibility.

        Returns:
            Dictionary with legacy config format
        """
        return {
            "LLM_PROVIDER": self.provider,
            "LLM_API_KEY": self.api_key,
            "MAX_CONTEXT_LENGTH": self.max_context_length,
            "EMBEDDING_MODEL": self.embedding_model,
            "LLM_MODEL": self.model,
            "MAX_RETRIES": self.max_retries,
            "RETRY_DELAY": self.retry_delay,
            "TOKEN_WARNING_THRESHOLD": self.token_warning_threshold,
            "SESSION_TIMEOUT": self.session_timeout,
            "DATA_DIR": str(self.data_dir),
            "PROJECTS_DB_PATH": str(self.projects_db_path),
            "VECTOR_DB_PATH": str(self.vector_db_path),
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"SocratesConfig("
            f"provider={self.provider}, "
            f"model={self.model}, "
            f"data_dir={self.data_dir}, "
            f"log_level={self.log_level})"
        )


class ConfigBuilder:
    """
    Fluent API for building SocratesConfig instances.

    Supports multiple LLM providers (anthropic, openai, google, ollama).

    Example:
        config = (ConfigBuilder("sk-...")
                  .with_provider("anthropic")
                  .with_data_dir("/path")
                  .with_model("claude-opus-4-5-20251101")
                  .build())
    """

    def __init__(self, api_key: str) -> None:
        """Initialize builder with API key"""
        self._config_dict: Dict[str, Any] = {"api_key": api_key}

    def with_provider(self, provider: str) -> "ConfigBuilder":
        """Set LLM provider (anthropic, openai, google, ollama)"""
        self._config_dict["provider"] = provider
        return self

    def with_data_dir(self, data_dir: Union[str, Path]) -> "ConfigBuilder":
        """Set data directory"""
        self._config_dict["data_dir"] = data_dir
        return self

    def with_model(self, model: str) -> "ConfigBuilder":
        """Set LLM model identifier"""
        self._config_dict["model"] = model
        return self

    def with_embedding_model(self, model: str) -> "ConfigBuilder":
        """Set embedding model"""
        self._config_dict["embedding_model"] = model
        return self

    def with_log_level(self, level: str) -> "ConfigBuilder":
        """Set log level"""
        self._config_dict["log_level"] = level
        return self

    def with_log_file(self, log_file: Union[str, Path]) -> "ConfigBuilder":
        """Set log file path"""
        self._config_dict["log_file"] = log_file
        return self

    def with_custom_knowledge(self, knowledge: List[str]) -> "ConfigBuilder":
        """Set custom knowledge entries"""
        self._config_dict["custom_knowledge"] = knowledge
        return self

    def with_max_context_length(self, length: int) -> "ConfigBuilder":
        """Set max context length"""
        self._config_dict["max_context_length"] = length
        return self

    def with_max_retries(self, retries: int) -> "ConfigBuilder":
        """Set max retries"""
        self._config_dict["max_retries"] = retries
        return self

    def with_retry_delay(self, delay: float) -> "ConfigBuilder":
        """Set retry delay"""
        self._config_dict["retry_delay"] = delay
        return self

    def build(self) -> SocratesConfig:
        """Build and return the SocratesConfig instance"""
        return SocratesConfig(**self._config_dict)
