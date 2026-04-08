"""
Database Client Interface and Implementations.

Provides abstract DatabaseClient interface and concrete implementations
(SQLite, PostgreSQL, etc.) for persistent data storage across all Socratic services.
"""

import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .connection_pool import SQLiteConnectionPool


class DatabaseClient(ABC):
    """Abstract database client interface for all Socratic services."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    async def initialize_schema(self) -> None:
        """Initialize database schema if needed."""
        pass

    @abstractmethod
    async def save_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> bool:
        """Save or update an entity."""
        pass

    @abstractmethod
    async def load_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Load an entity by ID."""
        pass

    @abstractmethod
    async def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity by ID."""
        pass

    @abstractmethod
    async def query_entities(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query entities with optional filtering."""
        pass

    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw query."""
        pass

    @abstractmethod
    async def transaction(self) -> Any:
        """Start a transaction context."""
        pass


class SQLiteClient(DatabaseClient):
    """SQLite implementation of DatabaseClient."""

    def __init__(
        self,
        db_path: str = ":memory:",
        pool_enabled: bool = True,
        pool_size: int = 5,
        max_overflow: int = 3,
        pool_timeout: float = 30.0,
    ):
        """
        Initialize SQLite client.

        Args:
            db_path: Path to SQLite database file or ":memory:" for in-memory DB
            pool_enabled: Enable connection pooling
            pool_size: Number of connections in pool
            max_overflow: Maximum connections above pool_size
            pool_timeout: Timeout for acquiring connection from pool
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.pool_enabled = pool_enabled
        self.pool: Optional[SQLiteConnectionPool] = None
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout

        self._db_lock = threading.RLock()

    async def connect(self) -> None:
        """Establish SQLite connection."""
        if not self.db_path.startswith(":memory:"):
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        if self.pool_enabled and self.db_path != ":memory:":
            # Use connection pooling
            self.pool = SQLiteConnectionPool(
                db_path=self.db_path,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                timeout=self.pool_timeout,
                echo=False,
            )
            await self.pool.initialize()
            # Get one connection for schema initialization
            async with self.pool.get_connection() as conn:
                self.connection = conn
        else:
            # Use single connection (in-memory or pool disabled)
            # Thread-safe direct connection
            with self._db_lock:
                self.connection = sqlite3.connect(str(self.db_path), timeout=30)
            if self.connection:
                self.connection.row_factory = sqlite3.Row
                self.connection.execute("PRAGMA foreign_keys = ON")
                self.connection.execute("PRAGMA journal_mode = WAL")

    async def disconnect(self) -> None:
        """Close SQLite connection."""
        if self.pool:
            await self.pool.close_all()
            self.pool = None
        elif self.connection:
            self.connection.close()
        self.connection = None

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        if self.pool:
            return self.pool.get_stats()
        return {"pool_enabled": False}

    async def initialize_schema(self) -> None:
        """Initialize database schema for all Socratic entities."""
        if not self.connection:
            await self.connect()

        assert self.connection is not None
        cursor = self.connection.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT,
                subscription_tier TEXT DEFAULT 'free',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
            """
        )

        # Projects table
        cursor.execute(
            """
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
            )
            """
        )

        # Sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                project_id TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                metadata TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            )
            """
        )

        # Interactions table
        cursor.execute(
            """
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
            )
            """
        )

        # Questions table
        cursor.execute(
            """
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
            )
            """
        )

        # Patterns table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT,
                detected_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
            """
        )

        # Metrics table
        cursor.execute(
            """
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
            )
            """
        )

        # Recommendations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                recommendation_type TEXT,
                content TEXT,
                confidence REAL,
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
            """
        )

        assert self.connection is not None
        self.connection.commit()

    async def save_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> bool:
        """Save or update an entity."""
        if not self.connection:
            await self.connect()

        assert self.connection is not None

        import json

        cursor = self.connection.cursor()
        data_copy = dict(data)

        if entity_type == "user":
            data_copy.setdefault("created_at", datetime.utcnow().isoformat())
            data_copy.setdefault("updated_at", datetime.utcnow().isoformat())
            cursor.execute(
                """
                INSERT OR REPLACE INTO users
                (user_id, username, email, subscription_tier, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_id,
                    data_copy.get("username"),
                    data_copy.get("email"),
                    data_copy.get("subscription_tier", "free"),
                    data_copy.get("created_at"),
                    data_copy.get("updated_at"),
                    json.dumps(data_copy.get("metadata", {})),
                ),
            )
        elif entity_type == "project":
            data_copy.setdefault("created_at", datetime.utcnow().isoformat())
            data_copy.setdefault("updated_at", datetime.utcnow().isoformat())
            cursor.execute(
                """
                INSERT OR REPLACE INTO projects
                (project_id, user_id, name, phase, description, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_id,
                    data_copy.get("user_id"),
                    data_copy.get("name"),
                    data_copy.get("phase", "discovery"),
                    data_copy.get("description"),
                    data_copy.get("created_at"),
                    data_copy.get("updated_at"),
                    json.dumps(data_copy.get("metadata", {})),
                ),
            )
        elif entity_type == "interaction":
            cursor.execute(
                """
                INSERT OR REPLACE INTO interactions
                (interaction_id, session_id, user_id, agent_name, agent_type,
                 input_data, output_data, status, timestamp, duration_ms, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_id,
                    data_copy.get("session_id"),
                    data_copy.get("user_id"),
                    data_copy.get("agent_name"),
                    data_copy.get("agent_type"),
                    json.dumps(data_copy.get("input_data", {})),
                    json.dumps(data_copy.get("output_data", {})),
                    data_copy.get("status", "in_progress"),
                    data_copy.get("timestamp", datetime.utcnow().isoformat()),
                    data_copy.get("duration_ms"),
                    data_copy.get("error_message"),
                    json.dumps(data_copy.get("metadata", {})),
                ),
            )
        elif entity_type == "question":
            cursor.execute(
                """
                INSERT OR REPLACE INTO questions
                (question_id, project_id, phase, question, status, answer,
                 created_at, answered_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_id,
                    data_copy.get("project_id"),
                    data_copy.get("phase"),
                    data_copy.get("question"),
                    data_copy.get("status", "unanswered"),
                    data_copy.get("answer"),
                    data_copy.get("created_at", datetime.utcnow().isoformat()),
                    data_copy.get("answered_at"),
                    json.dumps(data_copy.get("metadata", {})),
                ),
            )

        assert self.connection is not None
        self.connection.commit()
        return True

    async def load_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Load an entity by ID."""
        if not self.connection:
            await self.connect()

        assert self.connection is not None

        import json

        cursor = self.connection.cursor()

        if entity_type == "user":
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (entity_id,))
        elif entity_type == "project":
            cursor.execute("SELECT * FROM projects WHERE project_id = ?", (entity_id,))
        elif entity_type == "interaction":
            cursor.execute("SELECT * FROM interactions WHERE interaction_id = ?", (entity_id,))
        elif entity_type == "question":
            cursor.execute("SELECT * FROM questions WHERE question_id = ?", (entity_id,))
        else:
            return None

        row = cursor.fetchone()
        if not row:
            return None

        result = dict(row)
        # Parse JSON fields
        for key in result:
            if isinstance(result[key], str) and key.endswith("_data"):
                try:
                    result[key] = json.loads(result[key])
                except (json.JSONDecodeError, TypeError):
                    pass
            elif key == "metadata":
                try:
                    result[key] = json.loads(result[key]) if result[key] else {}
                except (json.JSONDecodeError, TypeError):
                    result[key] = {}

        return result

    async def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity by ID."""
        if not self.connection:
            await self.connect()

        assert self.connection is not None
        cursor = self.connection.cursor()

        if entity_type == "user":
            cursor.execute("DELETE FROM users WHERE user_id = ?", (entity_id,))
        elif entity_type == "project":
            cursor.execute("DELETE FROM projects WHERE project_id = ?", (entity_id,))
        elif entity_type == "interaction":
            cursor.execute("DELETE FROM interactions WHERE interaction_id = ?", (entity_id,))
        elif entity_type == "question":
            cursor.execute("DELETE FROM questions WHERE question_id = ?", (entity_id,))
        else:
            return False

        assert self.connection is not None
        self.connection.commit()
        return cursor.rowcount > 0

    async def query_entities(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query entities with optional filtering."""
        if not self.connection:
            await self.connect()

        assert self.connection is not None

        import json

        cursor = self.connection.cursor()
        filters = filters or {}

        if entity_type == "user":
            query = "SELECT * FROM users"
        elif entity_type == "project":
            query = "SELECT * FROM projects"
        elif entity_type == "interaction":
            query = "SELECT * FROM interactions"
        elif entity_type == "question":
            query = "SELECT * FROM questions"
        else:
            return []

        # Add filters
        where_clauses = []
        params = []
        for key, value in filters.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        # Validate and add LIMIT/OFFSET safely
        # LIMIT and OFFSET must be integers to prevent SQL injection
        if limit:
            if not isinstance(limit, int) or limit < 0:
                raise ValueError("LIMIT must be a non-negative integer")
            query += f" LIMIT {limit}"
        if offset:
            if not isinstance(offset, int) or offset < 0:
                raise ValueError("OFFSET must be a non-negative integer")
            query += f" OFFSET {offset}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            for key in result:
                if isinstance(result[key], str) and key.endswith("_data"):
                    try:
                        result[key] = json.loads(result[key])
                    except (json.JSONDecodeError, TypeError):
                        pass
                elif key == "metadata":
                    try:
                        result[key] = json.loads(result[key]) if result[key] else {}
                    except (json.JSONDecodeError, TypeError):
                        result[key] = {}
            results.append(result)

        return results

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw query."""
        if not self.connection:
            await self.connect()

        assert self.connection is not None
        cursor = self.connection.cursor()
        cursor.execute(query, params or {})
        self.connection.commit()
        return cursor.fetchall()

    async def transaction(self) -> Any:
        """Start a transaction context."""
        if not self.connection:
            await self.connect()
        return self.connection


class PostgresClient(DatabaseClient):
    """PostgreSQL implementation of DatabaseClient (stub for future use)."""

    def __init__(self, connection_string: str):
        self._db_lock = threading.RLock()
        """
        Initialize PostgreSQL client.

        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.connection: Optional[Any] = None

    async def connect(self) -> None:
        """Establish PostgreSQL connection."""
        raise NotImplementedError("PostgreSQL support coming in future version")

    async def disconnect(self) -> None:
        """Close PostgreSQL connection."""
        raise NotImplementedError("PostgreSQL support coming in future version")

    async def initialize_schema(self) -> None:
        """Initialize database schema."""
        raise NotImplementedError("PostgreSQL support coming in future version")

    async def save_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> bool:
        """Save or update an entity."""
        raise NotImplementedError("PostgreSQL support coming in future version")

    async def load_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Load an entity by ID."""
        raise NotImplementedError("PostgreSQL support coming in future version")

    async def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity by ID."""
        raise NotImplementedError("PostgreSQL support coming in future version")

    async def query_entities(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query entities with optional filtering."""
        raise NotImplementedError("PostgreSQL support coming in future version")

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw query."""
        raise NotImplementedError("PostgreSQL support coming in future version")

    async def transaction(self) -> Any:
        """Start a transaction context."""
        raise NotImplementedError("PostgreSQL support coming in future version")
