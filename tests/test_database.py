"""
Tests for database client implementations.
"""

import pytest

from socratic_core.database import DatabaseClient, SQLiteClient


@pytest.fixture
async def db_client():
    """Create an in-memory SQLite client for testing."""
    client = SQLiteClient(":memory:")
    await client.connect()
    await client.initialize_schema()
    yield client
    await client.disconnect()


@pytest.mark.asyncio
async def test_sqlite_connection():
    """Test SQLite connection."""
    client = SQLiteClient(":memory:")
    await client.connect()
    assert client.connection is not None
    await client.disconnect()


@pytest.mark.asyncio
async def test_schema_initialization():
    """Test database schema initialization."""
    client = SQLiteClient(":memory:")
    await client.connect()
    await client.initialize_schema()

    # Check that tables exist
    cursor = client.connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = [
        "users",
        "projects",
        "sessions",
        "interactions",
        "questions",
        "patterns",
        "metrics",
        "recommendations",
    ]

    for table in expected_tables:
        assert table in tables, f"Table {table} not created"

    await client.disconnect()


@pytest.mark.asyncio
async def test_save_and_load_user(db_client):
    """Test saving and loading a user."""
    user_data = {
        "username": "test_user",
        "email": "test@example.com",
        "subscription_tier": "pro",
    }

    # Save user
    success = await db_client.save_entity("user", "usr_123", user_data)
    assert success is True

    # Load user
    loaded = await db_client.load_entity("user", "usr_123")
    assert loaded is not None
    assert loaded["username"] == "test_user"
    assert loaded["email"] == "test@example.com"
    assert loaded["subscription_tier"] == "pro"


@pytest.mark.asyncio
async def test_save_and_load_project(db_client):
    """Test saving and loading a project."""
    # First create the user that the project will reference
    user_data = {
        "username": "test_user",
        "email": "test@example.com",
        "subscription_tier": "pro",
    }
    await db_client.save_entity("user", "usr_123", user_data)

    project_data = {
        "user_id": "usr_123",
        "name": "My Project",
        "phase": "discovery",
        "description": "Test project",
    }

    # Save project
    success = await db_client.save_entity("project", "proj_123", project_data)
    assert success is True

    # Load project
    loaded = await db_client.load_entity("project", "proj_123")
    assert loaded is not None
    assert loaded["name"] == "My Project"
    assert loaded["phase"] == "discovery"


@pytest.mark.asyncio
async def test_save_and_load_question(db_client):
    """Test saving and loading a question."""
    # First create the user and project that the question will reference
    user_data = {"username": "test_user", "email": "test@example.com"}
    await db_client.save_entity("user", "usr_123", user_data)

    project_data = {"user_id": "usr_123", "name": "My Project", "phase": "discovery"}
    await db_client.save_entity("project", "proj_123", project_data)

    question_data = {
        "project_id": "proj_123",
        "phase": "discovery",
        "question": "What is the purpose of your project?",
        "status": "unanswered",
    }

    # Save question
    success = await db_client.save_entity("question", "q_123", question_data)
    assert success is True

    # Load question
    loaded = await db_client.load_entity("question", "q_123")
    assert loaded is not None
    assert loaded["question"] == "What is the purpose of your project?"
    assert loaded["status"] == "unanswered"


@pytest.mark.asyncio
async def test_query_entities(db_client):
    """Test querying entities with filters."""
    # First create the user
    user_data = {"username": "test_user", "email": "test@example.com"}
    await db_client.save_entity("user", "usr_123", user_data)

    # Save multiple projects
    for i in range(3):
        project_data = {
            "user_id": "usr_123",
            "name": f"Project {i}",
            "phase": "discovery" if i % 2 == 0 else "implementation",
        }
        await db_client.save_entity("project", f"proj_{i}", project_data)

    # Query projects by phase
    projects = await db_client.query_entities("project", filters={"phase": "discovery"})
    assert len(projects) == 2


@pytest.mark.asyncio
async def test_delete_entity(db_client):
    """Test deleting an entity."""
    # Save a user
    user_data = {"username": "test_user", "email": "test@example.com"}
    await db_client.save_entity("user", "usr_123", user_data)

    # Verify it exists
    loaded = await db_client.load_entity("user", "usr_123")
    assert loaded is not None

    # Delete it
    success = await db_client.delete_entity("user", "usr_123")
    assert success is True

    # Verify it's gone
    loaded = await db_client.load_entity("user", "usr_123")
    assert loaded is None


@pytest.mark.asyncio
async def test_save_interaction(db_client):
    """Test saving an interaction."""
    # First create the user
    user_data = {"username": "test_user", "email": "test@example.com"}
    await db_client.save_entity("user", "usr_123", user_data)

    interaction_data = {
        "user_id": "usr_123",
        "agent_name": "SocraticCounselor",
        "agent_type": "counselor",
        "status": "completed",
        "input_data": {"topic": "Python"},
        "output_data": {"question": "What is Python?"},
    }

    # Save interaction
    success = await db_client.save_entity("interaction", "int_123", interaction_data)
    assert success is True

    # Load interaction
    loaded = await db_client.load_entity("interaction", "int_123")
    assert loaded is not None
    assert loaded["agent_name"] == "SocraticCounselor"
    assert loaded["status"] == "completed"


@pytest.mark.asyncio
async def test_abstract_interface():
    """Test that DatabaseClient is abstract."""
    # Should not be able to instantiate abstract class
    with pytest.raises(TypeError):
        DatabaseClient()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
