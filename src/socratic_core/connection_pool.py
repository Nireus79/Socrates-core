"""Connection pooling for efficient database resource management."""

import asyncio
import sqlite3
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PoolStats:
    """Statistics for connection pool."""

    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_requests: int = 0
    total_releases: int = 0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class ConnectionPool:
    """Generic connection pool for managing database connections."""

    def __init__(
        self,
        create_connection_func,
        pool_size: int = 10,
        max_overflow: int = 5,
        timeout: float = 30.0,
        echo: bool = False,
    ):
        """
        Initialize connection pool.

        Args:
            create_connection_func: Function to create new connections
            pool_size: Number of connections to maintain
            max_overflow: Maximum connections above pool_size
            timeout: Timeout for acquiring connection
            echo: Log connection events
        """
        self.create_connection_func = create_connection_func
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        self.echo = echo

        self._available: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self._in_use: set = set()
        self._stats = PoolStats()
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the pool with initial connections."""
        async with self._lock:
            if self._initialized:
                return

            for _ in range(self.pool_size):
                conn = self.create_connection_func()
                await self._available.put(conn)
                self._stats.total_connections += 1

            self._initialized = True
            if self.echo:
                logger.info(f"Pool initialized with {self.pool_size} connections")

    @asynccontextmanager
    async def get_connection(self, timeout: Optional[float] = None):
        """
        Get a connection from the pool.

        Args:
            timeout: Override default timeout

        Yields:
            Database connection
        """
        timeout = timeout or self.timeout

        if not self._initialized:
            await self.initialize()

        # Try to get from pool
        try:
            conn = self._available.get_nowait()
        except asyncio.QueueEmpty:
            # Create overflow connection if allowed
            if len(self._in_use) < self.pool_size + self.max_overflow:
                conn = self.create_connection_func()
                self._stats.total_connections += 1
                if self.echo:
                    logger.debug(f"Created overflow connection. Total: {self._stats.total_connections}")
            else:
                # Wait for available connection
                try:
                    conn = await asyncio.wait_for(
                        self._available.get(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Could not acquire connection within {timeout}s")

        self._in_use.add(conn)
        self._stats.active_connections = len(self._in_use)
        self._stats.total_requests += 1

        if self.echo:
            logger.debug(f"Connection acquired. Active: {self._stats.active_connections}")

        try:
            yield conn
        finally:
            # Return connection to pool
            self._in_use.discard(conn)
            try:
                self._available.put_nowait(conn)
            except asyncio.QueueFull:
                # Connection was overflow, close it
                if hasattr(conn, 'close'):
                    conn.close()
                self._stats.total_connections -= 1
                if self.echo:
                    logger.debug(f"Closed overflow connection. Total: {self._stats.total_connections}")

            self._stats.idle_connections = self._available.qsize()
            self._stats.total_releases += 1

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            # Close idle connections
            while not self._available.empty():
                try:
                    conn = self._available.get_nowait()
                    if hasattr(conn, 'close'):
                        conn.close()
                except asyncio.QueueEmpty:
                    break

            # Close in-use connections
            for conn in self._in_use.copy():
                if hasattr(conn, 'close'):
                    conn.close()

            self._in_use.clear()
            self._stats.total_connections = 0
            self._stats.active_connections = 0
            self._stats.idle_connections = 0

            if self.echo:
                logger.info("All connections closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "total_connections": self._stats.total_connections,
            "active_connections": self._stats.active_connections,
            "idle_connections": self._stats.idle_connections,
            "total_requests": self._stats.total_requests,
            "total_releases": self._stats.total_releases,
            "created_at": self._stats.created_at.isoformat(),
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
        }

    async def health_check(self) -> bool:
        """Check if pool is healthy."""
        if not self._initialized:
            return False

        # Check if we have at least some available connections
        return self._available.qsize() > 0 or len(self._in_use) > 0


class SQLiteConnectionPool(ConnectionPool):
    """Specialized connection pool for SQLite."""

    def __init__(
        self,
        db_path: str = ":memory:",
        pool_size: int = 5,
        max_overflow: int = 3,
        timeout: float = 30.0,
        echo: bool = False,
    ):
        """
        Initialize SQLite connection pool.

        Args:
            db_path: Path to SQLite database
            pool_size: Number of connections to maintain
            max_overflow: Maximum connections above pool_size
            timeout: Timeout for acquiring connection
            echo: Log connection events
        """
        self.db_path = db_path

        def create_sqlite_connection():
            conn = sqlite3.connect(db_path, check_same_thread=False, timeout=timeout)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for concurrency
            return conn

        super().__init__(
            create_connection_func=create_sqlite_connection,
            pool_size=pool_size,
            max_overflow=max_overflow,
            timeout=timeout,
            echo=echo,
        )


class PostgresConnectionPool(ConnectionPool):
    """Specialized connection pool for PostgreSQL (requires psycopg2)."""

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 10,
        max_overflow: int = 5,
        timeout: float = 30.0,
        echo: bool = False,
    ):
        """
        Initialize PostgreSQL connection pool.

        Args:
            connection_string: PostgreSQL connection string
            pool_size: Number of connections to maintain
            max_overflow: Maximum connections above pool_size
            timeout: Timeout for acquiring connection
            echo: Log connection events
        """
        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL connection pooling")

        self.connection_string = connection_string

        def create_postgres_connection():
            conn = psycopg2.connect(connection_string, connect_timeout=timeout)
            conn.autocommit = False
            return conn

        super().__init__(
            create_connection_func=create_postgres_connection,
            pool_size=pool_size,
            max_overflow=max_overflow,
            timeout=timeout,
            echo=echo,
        )
