"""Tests for CLI-based import functions.

These tests use BdClient in dry_run mode to verify the conversion
logic without actually calling bd.
"""

import pytest

from speckit_to_beads.bd_client import BdClient
from speckit_to_beads.converter import import_tasks, import_spec
from speckit_to_beads.parsers import parse_tasks_file, parse_spec_file


class TestBdClient:
    """Tests for BdClient."""

    def test_dry_run_create(self):
        """Dry-run mode returns mock IDs."""
        client = BdClient(dry_run=True)
        result = client.create("Test issue")

        assert result.id.startswith("dry-")
        assert result.title == "Test issue"

    def test_dry_run_create_with_options(self):
        """Dry-run respects all create options."""
        client = BdClient(dry_run=True)
        result = client.create(
            "Test issue",
            description="Description",
            priority=1,
            issue_type="bug",
            labels=["label1", "label2"],
            external_ref="speckit:T001",
        )

        assert result.id.startswith("dry-")
        assert result.external_ref == "speckit:T001"

    def test_dry_run_dependency(self):
        """Dry-run mode handles dependencies."""
        client = BdClient(dry_run=True)
        result = client.add_dependency("dry-1", "dry-2", "blocks")

        assert result.from_id == "dry-1"
        assert result.to_id == "dry-2"
        assert result.dep_type == "blocks"

    def test_unique_ids_in_dry_run(self):
        """Each dry-run create gets a unique ID."""
        client = BdClient(dry_run=True)
        id1 = client.create("Issue 1").id
        id2 = client.create("Issue 2").id
        id3 = client.create("Issue 3").id

        assert id1 != id2 != id3


class TestImportTasks:
    """Tests for import_tasks function."""

    def test_import_simple_tasks(self, tasks_simple_content: str):
        """Import creates all tasks with correct IDs."""
        client = BdClient(dry_run=True)
        parsed = parse_tasks_file(tasks_simple_content)
        result = import_tasks(parsed, client)

        assert result.success
        assert len(result.created) == 9
        assert "T001" in result.id_map
        assert "T009" in result.id_map

    def test_import_builds_id_map(self, tasks_simple_content: str):
        """Import builds speckit ID → beads ID mapping."""
        client = BdClient(dry_run=True)
        parsed = parse_tasks_file(tasks_simple_content)
        result = import_tasks(parsed, client)

        # Each speckit ID maps to a unique beads ID
        assert len(result.id_map) == 9
        beads_ids = list(result.id_map.values())
        assert len(beads_ids) == len(set(beads_ids))  # All unique

    def test_import_resolves_dependencies(self, tasks_simple_content: str):
        """Import resolves dependencies to beads IDs."""
        client = BdClient(dry_run=True)
        parsed = parse_tasks_file(tasks_simple_content)
        result = import_tasks(parsed, client)

        # T006 depends on T005, T007 depends on T006
        # These should be added as dependencies with resolved IDs
        assert result.dependencies_added > 0
        assert result.success

    def test_import_with_epic(self, tasks_simple_content: str):
        """Import can link all tasks to an epic."""
        client = BdClient(dry_run=True)
        parsed = parse_tasks_file(tasks_simple_content)
        result = import_tasks(parsed, client, epic_id="bd-epic-1")

        assert result.success
        # All tasks should be created with parent=epic
        # (We can't directly verify in dry-run, but no errors means it worked)

    def test_import_with_progress_callback(self, tasks_simple_content: str):
        """Import calls progress callback."""
        client = BdClient(dry_run=True)
        parsed = parse_tasks_file(tasks_simple_content)

        progress_calls: list[tuple[str, str]] = []

        def on_progress(action: str, message: str) -> None:
            progress_calls.append((action, message))

        result = import_tasks(parsed, client, on_progress=on_progress)

        assert result.success
        assert len(progress_calls) > 0
        # Should have phase announcements
        actions = [c[0] for c in progress_calls]
        assert "phase" in actions
        assert "created" in actions


class TestImportSpec:
    """Tests for import_spec function."""

    def test_import_user_stories(self, spec_simple_content: str):
        """Import creates user stories."""
        client = BdClient(dry_run=True)
        parsed = parse_spec_file(spec_simple_content)
        result = import_spec(parsed, client)

        assert result.success
        assert len(result.created) == 3  # 3 user stories in fixture
        assert "US1" in result.id_map
        assert "US2" in result.id_map
        assert "US3" in result.id_map

    def test_import_spec_with_epic(self, spec_simple_content: str):
        """Import can link stories to an epic."""
        client = BdClient(dry_run=True)
        parsed = parse_spec_file(spec_simple_content)
        result = import_spec(parsed, client, epic_id="bd-feature-epic")

        assert result.success
        assert len(result.created) == 3


class TestErrorHandling:
    """Tests for error handling."""

    def test_missing_dependency_reported(self):
        """Missing dependency is reported as error."""
        client = BdClient(dry_run=True)

        # Create a parsed tasks file with a dependency on a non-existent task
        from speckit_to_beads.models import SpecKitTask, SpecKitTasksFile, SpecKitPhase

        tasks_file = SpecKitTasksFile(
            feature_name="Test",
            phases=[
                SpecKitPhase(
                    number=1,
                    title="Setup",
                    tasks=[
                        SpecKitTask(
                            id="T001",
                            description="Task 1",
                            dependencies=["T999"],  # Non-existent
                        ),
                    ],
                )
            ],
        )

        result = import_tasks(tasks_file, client)

        # Should have an error about missing dependency
        assert not result.success
        assert any("T999" in e for e in result.errors)

    def test_partial_success_continues(self):
        """Conversion continues after individual failures."""
        client = BdClient(dry_run=True)

        from speckit_to_beads.models import SpecKitTask, SpecKitTasksFile, SpecKitPhase

        tasks_file = SpecKitTasksFile(
            feature_name="Test",
            phases=[
                SpecKitPhase(
                    number=1,
                    title="Setup",
                    tasks=[
                        SpecKitTask(id="T001", description="Task 1"),
                        SpecKitTask(id="T002", description="Task 2", dependencies=["T999"]),
                        SpecKitTask(id="T003", description="Task 3"),
                    ],
                )
            ],
        )

        result = import_tasks(tasks_file, client)

        # Should create T001 and T003, report error for T002's dependency
        assert len(result.created) == 3
        assert "T001" in result.id_map
        assert "T003" in result.id_map
        assert not result.success  # Has errors


class TestIdempotency:
    """Tests for idempotency via external_ref."""

    def test_external_ref_set(self, tasks_simple_content: str):
        """Import sets external_ref for each task."""
        client = BdClient(dry_run=True)
        parsed = parse_tasks_file(tasks_simple_content)
        result = import_tasks(parsed, client)

        # Verify external_ref is set (we check via the CreatedIssue)
        for created in result.created:
            assert created.external_ref is not None
            assert created.external_ref.startswith("speckit:")
