"""Tests for spec-kit to beads converter."""

import json

import pytest

from speckit_to_beads.converter import (
    task_to_bead,
    tasks_file_to_beads,
    user_story_to_bead,
    spec_file_to_beads,
    to_jsonl,
)
from speckit_to_beads.parsers import parse_tasks_file, parse_spec_file


class TestTaskToBead:
    """Tests for individual task conversion."""

    def test_simple_task(self):
        """Convert simple task to bead."""
        from speckit_to_beads.models import SpecKitTask

        task = SpecKitTask(
            id="T001",
            status="open",
            parallel=False,
            user_story=None,
            description="Create project structure",
            file_path=None,
            dependencies=[],
            phase=1,
            phase_title="Setup",
        )

        bead = task_to_bead(task)

        assert bead.title == "T001: Create project structure"
        assert bead.status == "open"
        assert bead.issue_type == "task"
        assert "speckit:T001" in bead.labels
        assert "phase:1" in bead.labels
        assert "parallel" not in bead.labels

    def test_task_with_parallel(self):
        """Parallel tasks get the parallel label."""
        from speckit_to_beads.models import SpecKitTask

        task = SpecKitTask(
            id="T002",
            status="open",
            parallel=True,
            user_story=None,
            description="Configure linting",
            file_path=None,
            dependencies=[],
        )

        bead = task_to_bead(task)

        assert "parallel" in bead.labels
        assert "speckit:T002" in bead.labels

    def test_task_with_user_story(self):
        """Tasks with user story get the story label."""
        from speckit_to_beads.models import SpecKitTask

        task = SpecKitTask(
            id="T005",
            status="open",
            parallel=False,
            user_story="US1",
            description="Create User model",
            file_path="src/models/user.py",
            dependencies=[],
        )

        bead = task_to_bead(task)

        assert "US1" in bead.labels
        assert "src/models/user.py" in bead.description

    def test_task_with_dependencies(self):
        """Dependencies are converted to beads format."""
        from speckit_to_beads.models import SpecKitTask

        task = SpecKitTask(
            id="T006",
            status="open",
            parallel=False,
            user_story="US1",
            description="Implement AuthService",
            file_path="src/services/auth.py",
            dependencies=["T005"],
        )

        bead = task_to_bead(task)

        assert len(bead.dependencies) == 1
        assert bead.dependencies[0].depends_on_id == "T005"
        assert bead.dependencies[0].type == "blocks"

    def test_closed_task(self):
        """Closed tasks have closed status."""
        from speckit_to_beads.models import SpecKitTask

        task = SpecKitTask(
            id="T007",
            status="closed",
            parallel=True,
            user_story="US1",
            description="Add tests",
            file_path=None,
            dependencies=[],
        )

        bead = task_to_bead(task)

        assert bead.status == "closed"

    def test_task_with_epic_parent(self):
        """Task can be linked to an epic."""
        from speckit_to_beads.models import SpecKitTask

        task = SpecKitTask(
            id="T001",
            status="open",
            description="Task with parent",
        )

        bead = task_to_bead(task, epic_id="bd-42")

        # Check that parent dependency is added
        parent_deps = [d for d in bead.dependencies if d.type == "parent-child"]
        assert len(parent_deps) == 1
        assert parent_deps[0].depends_on_id == "bd-42"


class TestTasksFileToBead:
    """Tests for full tasks.md conversion."""

    def test_convert_simple_tasks(self, tasks_simple_content: str):
        """Convert simple tasks.md to beads."""
        tasks_file = parse_tasks_file(tasks_simple_content)
        beads = tasks_file_to_beads(tasks_file)

        assert len(beads) == 9  # Total tasks in fixture

        # Check first task
        t001 = next(b for b in beads if "speckit:T001" in b.labels)
        assert "T001:" in t001.title
        assert "phase:1" in t001.labels

        # Check parallel task
        t002 = next(b for b in beads if "speckit:T002" in b.labels)
        assert "parallel" in t002.labels

        # Check closed task
        t007 = next(b for b in beads if "speckit:T007" in b.labels)
        assert t007.status == "closed"

    def test_convert_with_epic(self, tasks_simple_content: str):
        """Convert with epic parent."""
        tasks_file = parse_tasks_file(tasks_simple_content)
        beads = tasks_file_to_beads(tasks_file, epic_id="bd-epic-1")

        # All tasks should have parent-child dependency to epic
        for bead in beads:
            parent_deps = [d for d in bead.dependencies if d.type == "parent-child"]
            assert len(parent_deps) == 1
            assert parent_deps[0].depends_on_id == "bd-epic-1"

    def test_convert_full_tasks(self, tasks_full_content: str):
        """Convert full tasks.md with complex dependencies."""
        tasks_file = parse_tasks_file(tasks_full_content)
        beads = tasks_file_to_beads(tasks_file)

        # Check task with dependencies
        t012 = next(b for b in beads if "speckit:T012" in b.labels)
        block_deps = [d for d in t012.dependencies if d.type == "blocks"]
        dep_ids = [d.depends_on_id for d in block_deps]
        assert "T005" in dep_ids
        assert "T006" in dep_ids


class TestUserStoryToBead:
    """Tests for user story conversion."""

    def test_user_story_basic(self, spec_simple_content: str):
        """Convert user story to bead."""
        spec = parse_spec_file(spec_simple_content)
        us1 = spec.user_stories[0]

        bead = user_story_to_bead(us1, feature_name="User Authentication")

        assert bead.title == "US1: Login Flow"
        assert bead.issue_type == "feature"
        assert bead.priority == 1  # P1 → 1
        assert "speckit:US1" in bead.labels
        assert "P1" in bead.labels

    def test_user_story_with_acceptance(self, spec_simple_content: str):
        """Acceptance criteria go into description."""
        spec = parse_spec_file(spec_simple_content)
        us1 = spec.user_stories[0]

        bead = user_story_to_bead(us1, feature_name="User Authentication")

        assert "Given" in bead.acceptance_criteria or "Given" in bead.description


class TestSpecFileToBead:
    """Tests for spec.md conversion."""

    def test_convert_spec(self, spec_simple_content: str):
        """Convert spec.md to beads."""
        spec = parse_spec_file(spec_simple_content)
        beads = spec_file_to_beads(spec)

        # Should have 3 user stories converted
        story_beads = [b for b in beads if b.issue_type == "feature"]
        assert len(story_beads) == 3

        # Check priorities
        us1 = next(b for b in beads if "speckit:US1" in b.labels)
        us2 = next(b for b in beads if "speckit:US2" in b.labels)
        assert us1.priority == 1
        assert us2.priority == 2


class TestToJsonl:
    """Tests for JSONL output."""

    def test_to_jsonl_format(self, tasks_simple_content: str):
        """Output is valid JSONL."""
        tasks_file = parse_tasks_file(tasks_simple_content)
        beads = tasks_file_to_beads(tasks_file)
        jsonl = to_jsonl(beads)

        lines = jsonl.strip().split("\n")
        assert len(lines) == 9

        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert "title" in data
            assert "status" in data

    def test_jsonl_no_empty_fields(self, tasks_simple_content: str):
        """JSONL doesn't include empty lists/None values."""
        tasks_file = parse_tasks_file(tasks_simple_content)
        beads = tasks_file_to_beads(tasks_file)
        jsonl = to_jsonl(beads)

        # T001 has no dependencies
        lines = jsonl.strip().split("\n")
        t001_line = next(l for l in lines if "T001" in l)
        t001_data = json.loads(t001_line)

        # Should not have empty dependencies array
        if "dependencies" in t001_data:
            assert len(t001_data["dependencies"]) > 0
