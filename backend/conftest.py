"""
Pytest configuration and fixtures for comprehensive testing suite.
"""
import asyncio
import os
import tempfile
import pytest
import sqlite3
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from core.database import get_db, Base
from core.redis_client import get_redis_client
from models.schemas import User, Document, Conversation


# Test database setup
@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override the get_db dependency."""
    def _override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    return _override_get_db


@pytest.fixture(scope="function")
def test_client(override_get_db):
    """Create a test client with overridden dependencies."""
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock Redis client
    mock_redis = AsyncMock()
    app.dependency_overrides[get_redis_client] = lambda: mock_redis
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def mock_redis():
    """Mock Redis client for testing."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    mock.expire.return_value = True
    return mock


@pytest.fixture(scope="function")
def mock_ollama():
    """Mock Ollama client for testing."""
    mock = MagicMock()
    mock.generate.return_value = {
        'response': 'Test response from Ollama',
        'done': True
    }
    mock.embeddings.return_value = {
        'embedding': [0.1] * 384
    }
    return mock


@pytest.fixture(scope="function")
def mock_vector_store():
    """Mock vector store for testing."""
    mock = AsyncMock()
    mock.add_documents.return_value = True
    mock.similarity_search.return_value = [
        {
            'content': 'Test document content',
            'metadata': {'source': 'test.pdf', 'page': 1},
            'score': 0.95
        }
    ]
    mock.delete_documents.return_value = True
    return mock


@pytest.fixture(scope="function")
def sample_user():
    """Create a sample user for testing."""
    return User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        is_active=True
    )


@pytest.fixture(scope="function")
def sample_document():
    """Create a sample document for testing."""
    return Document(
        id="test-doc-id",
        title="Test Document",
        content="This is a test document content.",
        file_path="/tmp/test.pdf",
        user_id="test-user-id",
        metadata={"pages": 1, "size": 1024}
    )


@pytest.fixture(scope="function")
def sample_conversation():
    """Create a sample conversation for testing."""
    return Conversation(
        id="test-conv-id",
        user_id="test-user-id",
        title="Test Conversation",
        messages=[]
    )


@pytest.fixture(scope="function")
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
        f.write(b"Test PDF content")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture(scope="function")
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Performance testing fixtures
@pytest.fixture(scope="function")
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Error simulation fixtures
@pytest.fixture(scope="function")
def simulate_db_error(monkeypatch):
    """Simulate database errors for testing error handling."""
    def mock_execute(*args, **kwargs):
        raise sqlite3.OperationalError("Database is locked")
    
    return mock_execute


@pytest.fixture(scope="function")
def simulate_network_error():
    """Simulate network errors for testing error handling."""
    def mock_request(*args, **kwargs):
        raise ConnectionError("Network unreachable")
    
    return mock_request


# Load testing fixtures
@pytest.fixture(scope="function")
def load_test_data():
    """Generate test data for load testing."""
    return {
        'users': [f"user_{i}" for i in range(100)],
        'documents': [f"document_{i}.pdf" for i in range(50)],
        'queries': [f"test query {i}" for i in range(200)]
    }


# Integration test fixtures
@pytest.fixture(scope="function")
async def integration_setup(test_db_session, mock_redis, mock_vector_store):
    """Setup for integration tests."""
    # Create test data in database
    test_user = User(
        id="integration-user",
        email="integration@test.com",
        username="integration_user",
        is_active=True
    )
    test_db_session.add(test_user)
    test_db_session.commit()
    
    return {
        'user': test_user,
        'redis': mock_redis,
        'vector_store': mock_vector_store
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    
    # Cleanup any test files that might have been created
    test_patterns = [
        "test_*.db",
        "test_*.json",
        "test_*.log",
        "*_test.pdf"
    ]
    
    import glob
    for pattern in test_patterns:
        for file in glob.glob(pattern):
            try:
                os.unlink(file)
            except OSError:
                pass