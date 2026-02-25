"""Shared test fixtures for speckit-to-beads tests."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def tasks_simple_path() -> Path:
    """Path to simple tasks.md fixture."""
    return FIXTURES_DIR / "tasks-simple.md"


@pytest.fixture
def tasks_simple_content(tasks_simple_path: Path) -> str:
    """Content of simple tasks.md fixture."""
    return tasks_simple_path.read_text()


@pytest.fixture
def tasks_full_path() -> Path:
    """Path to full tasks.md fixture."""
    return FIXTURES_DIR / "tasks-full.md"


@pytest.fixture
def tasks_full_content(tasks_full_path: Path) -> str:
    """Content of full tasks.md fixture."""
    return tasks_full_path.read_text()


@pytest.fixture
def spec_simple_path() -> Path:
    """Path to simple spec.md fixture."""
    return FIXTURES_DIR / "spec-simple.md"


@pytest.fixture
def spec_simple_content(spec_simple_path: Path) -> str:
    """Content of simple spec.md fixture."""
    return spec_simple_path.read_text()
