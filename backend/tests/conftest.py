"""Pytest fixtures for Career Intelligence backend tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db import models as db_models
from app.main import app as fastapi_app


@pytest.fixture
def client() -> TestClient:
    """Provides FastAPI test client fixture."""
    return TestClient(fastapi_app)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Provides an isolated in-memory database session fixture for testing."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
