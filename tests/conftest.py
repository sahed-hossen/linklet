"""
Shared pytest fixtures for the Linklet test suite.
All fixtures here are auto-discovered by pytest across all test files.
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure the backend package is importable
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Use a local SQLite DB for tests — no Supabase credentials required in CI
os.environ.setdefault("TEST_DATABASE_URL", "sqlite:///./test_shortener.db")

from database import Base, engine  # noqa: E402 (must come after env var is set)


@pytest.fixture(autouse=True)
def clean_db():
    """Reset the test database before and after every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
