"""Database migration utilities for schema versioning."""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Migration-related error."""

    pass


class Migration:
    """Represents a single database migration."""

    def __init__(self, version: str, description: str, up_sql: str, down_sql: str):
        """
        Initialize migration.

        Args:
            version: Migration version (e.g., "001")
            description: Human-readable description
            up_sql: SQL to apply migration
            down_sql: SQL to revert migration
        """
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.timestamp = datetime.utcnow().isoformat()

    def __repr__(self):
        return f"Migration({self.version}: {self.description})"


class MigrationRunner:
    """Runs database migrations."""

    def __init__(self, db_path: str):
        """
        Initialize migration runner.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.migrations: Dict[str, Migration] = {}

    def _ensure_migrations_table(self, conn: sqlite3.Connection) -> None:
        """Ensure migrations tracking table exists."""
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS __migrations__ (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                duration_ms REAL NOT NULL
            )
            """
        )
        conn.commit()

    def register_migration(self, migration: Migration) -> None:
        """Register a migration."""
        if migration.version in self.migrations:
            raise MigrationError(f"Migration {migration.version} already registered")
        self.migrations[migration.version] = migration

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        conn = sqlite3.connect(self.db_path)
        try:
            self._ensure_migrations_table(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM __migrations__ ORDER BY version")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        applied = set(self.get_applied_migrations())
        pending = []

        for version in sorted(self.migrations.keys()):
            if version not in applied:
                pending.append(self.migrations[version])

        return pending

    def apply_migration(self, migration: Migration) -> float:
        """
        Apply a migration.

        Args:
            migration: Migration to apply

        Returns:
            Duration in milliseconds

        Raises:
            MigrationError: If migration fails
        """
        conn = sqlite3.connect(self.db_path)
        start = datetime.utcnow()

        try:
            self._ensure_migrations_table(conn)
            cursor = conn.cursor()

            # Check if already applied
            cursor.execute(
                "SELECT 1 FROM __migrations__ WHERE version = ?",
                (migration.version,),
            )
            if cursor.fetchone():
                raise MigrationError(f"Migration {migration.version} already applied")

            # Apply migration
            cursor.executescript(migration.up_sql)

            # Record migration
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            cursor.execute(
                """
                INSERT INTO __migrations__ (version, description, applied_at, duration_ms)
                VALUES (?, ?, ?, ?)
                """,
                (
                    migration.version,
                    migration.description,
                    datetime.utcnow().isoformat(),
                    duration,
                ),
            )
            conn.commit()

            logger.info(
                f"Applied migration {migration.version}: {migration.description} ({duration:.2f}ms)"
            )
            return duration

        except Exception as e:
            conn.rollback()
            raise MigrationError(f"Failed to apply migration {migration.version}: {e}")
        finally:
            conn.close()

    def revert_migration(self, migration: Migration) -> float:
        """
        Revert a migration.

        Args:
            migration: Migration to revert

        Returns:
            Duration in milliseconds

        Raises:
            MigrationError: If revert fails
        """
        conn = sqlite3.connect(self.db_path)
        start = datetime.utcnow()

        try:
            self._ensure_migrations_table(conn)
            cursor = conn.cursor()

            # Check if applied
            cursor.execute(
                "SELECT 1 FROM __migrations__ WHERE version = ?",
                (migration.version,),
            )
            if not cursor.fetchone():
                raise MigrationError(f"Migration {migration.version} not applied")

            # Revert migration
            cursor.executescript(migration.down_sql)

            # Remove migration record
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            cursor.execute(
                "DELETE FROM __migrations__ WHERE version = ?",
                (migration.version,),
            )
            conn.commit()

            logger.info(
                f"Reverted migration {migration.version}: {migration.description} ({duration:.2f}ms)"
            )
            return duration

        except Exception as e:
            conn.rollback()
            raise MigrationError(f"Failed to revert migration {migration.version}: {e}")
        finally:
            conn.close()

    def migrate_up(self) -> Dict[str, float]:
        """
        Apply all pending migrations.

        Returns:
            Dictionary mapping migration version to duration
        """
        pending = self.get_pending_migrations()
        results = {}

        for migration in pending:
            duration = self.apply_migration(migration)
            results[migration.version] = duration

        return results

    def migrate_down(self, steps: int = 1) -> Dict[str, float]:
        """
        Revert migrations.

        Args:
            steps: Number of migrations to revert

        Returns:
            Dictionary mapping migration version to duration
        """
        applied = self.get_applied_migrations()
        results = {}

        for version in reversed(applied[-steps:]):
            migration = self.migrations[version]
            duration = self.revert_migration(migration)
            results[version] = duration

        return results

    def get_migration_status(self) -> Dict[str, any]:
        """Get migration status."""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        return {
            "applied_count": len(applied),
            "pending_count": len(pending),
            "total_count": len(self.migrations),
            "applied_migrations": applied,
            "pending_migrations": [m.version for m in pending],
        }


# Built-in migrations for Socratic Core

INITIAL_SCHEMA_UP = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT,
    subscription_tier TEXT DEFAULT 'free',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    phase TEXT DEFAULT 'discovery',
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    metadata TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(project_id) REFERENCES projects(project_id)
);

-- Interactions table
CREATE TABLE IF NOT EXISTS interactions (
    interaction_id TEXT PRIMARY KEY,
    session_id TEXT,
    user_id TEXT NOT NULL,
    agent_name TEXT,
    agent_type TEXT,
    input_data TEXT,
    output_data TEXT,
    status TEXT DEFAULT 'in_progress',
    timestamp TEXT NOT NULL,
    duration_ms REAL,
    error_message TEXT,
    metadata TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    question TEXT NOT NULL,
    status TEXT DEFAULT 'unanswered',
    answer TEXT,
    created_at TEXT NOT NULL,
    answered_at TEXT,
    metadata TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(project_id)
);

-- Patterns table
CREATE TABLE IF NOT EXISTS patterns (
    pattern_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_data TEXT,
    detected_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    metric_id TEXT PRIMARY KEY,
    session_id TEXT,
    user_id TEXT,
    metric_type TEXT NOT NULL,
    metric_value REAL,
    recorded_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- Recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    recommendation_type TEXT,
    content TEXT,
    confidence REAL,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
"""

INITIAL_SCHEMA_DOWN = """
DROP TABLE IF EXISTS __migrations__;
DROP TABLE IF EXISTS recommendations;
DROP TABLE IF EXISTS metrics;
DROP TABLE IF EXISTS patterns;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS interactions;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS users;
"""

EVENT_PERSISTENCE_UP = """
-- Events table for audit trail
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    source TEXT,
    data TEXT,
    timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
"""

EVENT_PERSISTENCE_DOWN = """
DROP TABLE IF EXISTS events;
"""

# Create migration objects
MIGRATION_001 = Migration(
    version="001",
    description="Initial schema with users, projects, sessions, interactions, questions",
    up_sql=INITIAL_SCHEMA_UP,
    down_sql=INITIAL_SCHEMA_DOWN,
)

MIGRATION_002 = Migration(
    version="002",
    description="Add event persistence for audit trail",
    up_sql=EVENT_PERSISTENCE_UP,
    down_sql=EVENT_PERSISTENCE_DOWN,
)


def get_default_migrations() -> Dict[str, Migration]:
    """Get default Socratic Core migrations."""
    return {
        "001": MIGRATION_001,
        "002": MIGRATION_002,
    }
