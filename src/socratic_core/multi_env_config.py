"""Multi-environment configuration management for dev/staging/production."""

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, cast

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Supported environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentProfile:
    """Configuration profile for an environment."""

    name: str
    environment: Environment
    database_path: str
    debug: bool = False
    log_level: str = "INFO"
    max_workers: int = 10
    request_timeout: int = 30
    cache_enabled: bool = True
    cache_ttl: int = 3600
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 100
    secret_config: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class EnvironmentManager:
    """Manages multi-environment configuration."""

    # Built-in profiles
    DEVELOPMENT_PROFILE = EnvironmentProfile(
        name="development",
        environment=Environment.DEVELOPMENT,
        database_path=":memory:",
        debug=True,
        log_level="DEBUG",
        max_workers=4,
        request_timeout=60,
        cache_enabled=False,
        rate_limit_enabled=False,
    )

    STAGING_PROFILE = EnvironmentProfile(
        name="staging",
        environment=Environment.STAGING,
        database_path="./data/socrates_staging.db",
        debug=True,
        log_level="INFO",
        max_workers=8,
        request_timeout=30,
        cache_enabled=True,
        cache_ttl=1800,
        rate_limit_enabled=True,
        rate_limit_per_minute=500,
    )

    PRODUCTION_PROFILE = EnvironmentProfile(
        name="production",
        environment=Environment.PRODUCTION,
        database_path="/var/lib/socrates/socrates_prod.db",
        debug=False,
        log_level="WARNING",
        max_workers=32,
        request_timeout=30,
        cache_enabled=True,
        cache_ttl=7200,
        rate_limit_enabled=True,
        rate_limit_per_minute=1000,
    )

    def __init__(self):
        """Initialize environment manager."""
        self._profiles: Dict[str, EnvironmentProfile] = {
            "development": self.DEVELOPMENT_PROFILE,
            "staging": self.STAGING_PROFILE,
            "production": self.PRODUCTION_PROFILE,
        }
        self._current_env: Optional[Environment] = None
        self._secret_store: Dict[str, str] = {}

    def load_environment(self) -> Environment:
        """
        Load current environment from SOCRATES_ENV variable.

        Returns:
            Current environment
        """
        env_str = os.getenv("SOCRATES_ENV", "development").lower()

        if env_str == "production":
            self._current_env = Environment.PRODUCTION
        elif env_str == "staging":
            self._current_env = Environment.STAGING
        else:
            self._current_env = Environment.DEVELOPMENT

        logger.info(f"Loaded environment: {self._current_env.value}")
        return self._current_env

    def get_profile(self, environment: Optional[Environment] = None) -> EnvironmentProfile:
        """
        Get configuration profile.

        Args:
            environment: Environment name (uses current if None)

        Returns:
            Configuration profile
        """
        if environment is None:
            environment = self._current_env or Environment.DEVELOPMENT

        profile_name = environment.value if isinstance(environment, Environment) else environment

        if profile_name not in self._profiles:
            raise ValueError(f"Unknown environment: {profile_name}")

        return self._profiles[profile_name]

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret from secure store.

        Args:
            key: Secret key
            default: Default value if not found

        Returns:
            Secret value or default
        """
        # Try from environment variable first (highest priority)
        env_var = f"SOCRATES_{key.upper()}"
        env_value = os.getenv(env_var)
        if env_value:
            return env_value

        # Try from secret store
        if key in self._secret_store:
            return self._secret_store[key]

        return default

    def set_secret(self, key: str, value: str) -> None:
        """
        Set secret in secure store.

        Args:
            key: Secret key
            value: Secret value
        """
        self._secret_store[key] = value
        logger.info(f"Secret '{key}' registered")

    def load_secrets_from_env(self, prefix: str = "SOCRATES_SECRET_") -> Dict[str, str]:
        """
        Load all secrets from environment variables.

        Args:
            prefix: Environment variable prefix

        Returns:
            Dictionary of secrets loaded
        """
        loaded = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                secret_key = key[len(prefix) :].lower()
                self._secret_store[secret_key] = value
                loaded[secret_key] = value

        logger.info(f"Loaded {len(loaded)} secrets from environment")
        return loaded

    def load_secrets_from_file(self, filepath: str) -> Dict[str, str]:
        """
        Load secrets from JSON file.

        Args:
            filepath: Path to secrets JSON file

        Returns:
            Dictionary of secrets loaded
        """
        try:
            with open(filepath, "r") as f:
                secrets = cast(Dict[str, str], json.load(f))

            self._secret_store.update(secrets)
            logger.info(f"Loaded {len(secrets)} secrets from {filepath}")
            return secrets

        except FileNotFoundError:
            logger.warning(f"Secrets file not found: {filepath}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in secrets file: {filepath}")
            return {}

    def register_profile(self, profile: EnvironmentProfile) -> None:
        """
        Register custom environment profile.

        Args:
            profile: Environment profile
        """
        self._profiles[profile.name] = profile
        logger.info(f"Registered environment profile: {profile.name}")

    def validate_configuration(self, environment: Optional[Environment] = None) -> Dict[str, Any]:
        """
        Validate configuration for environment.

        Args:
            environment: Environment to validate

        Returns:
            Validation results
        """
        profile = self.get_profile(environment)
        issues = []

        # Check database path exists or is creatable
        if profile.database_path != ":memory:":
            db_dir = os.path.dirname(profile.database_path)
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except PermissionError:
                    issues.append(f"Cannot create database directory: {db_dir}")

        # Check required secrets
        required_secrets = ["ANTHROPIC_API_KEY", "DATABASE_PASSWORD"]
        missing_secrets = [s for s in required_secrets if not self.get_secret(s)]

        if missing_secrets:
            issues.append(f"Missing secrets: {', '.join(missing_secrets)}")

        # Check settings
        if profile.max_workers < 1:
            issues.append("max_workers must be >= 1")

        if profile.request_timeout < 1:
            issues.append("request_timeout must be >= 1")

        return {
            "environment": profile.environment.value,
            "valid": len(issues) == 0,
            "issues": issues,
        }

    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """
        Export current configuration.

        Args:
            include_secrets: Include secrets in export

        Returns:
            Configuration dictionary
        """
        profile = self.get_profile()

        config = {
            "environment": profile.environment.value,
            "name": profile.name,
            "debug": profile.debug,
            "log_level": profile.log_level,
            "max_workers": profile.max_workers,
            "request_timeout": profile.request_timeout,
            "cache_enabled": profile.cache_enabled,
            "cache_ttl": profile.cache_ttl,
            "rate_limit_enabled": profile.rate_limit_enabled,
            "rate_limit_per_minute": profile.rate_limit_per_minute,
            "custom_settings": profile.custom_settings,
        }

        if include_secrets:
            config["secrets"] = self._secret_store

        return config

    def get_all_profiles(self) -> Dict[str, EnvironmentProfile]:
        """Get all registered profiles."""
        return self._profiles.copy()
