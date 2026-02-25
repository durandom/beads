"""Tests for CLI empty file handling.

These tests verify that the CLI exits with code 1 when no items are found,
and exits with code 0 when --allow-empty is used.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from speckit_to_beads.cli import app

runner = CliRunner()


class TestTasksEmptyHandling:
    """Tests for empty file handling in tasks command."""

    def test_empty_file_exits_1(self, tmp_path: Path):
        """Empty tasks file should exit with code 1."""
        empty_file = tmp_path / "empty-tasks.md"
        empty_file.write_text("")

        result = runner.invoke(app, ["tasks", str(empty_file)])

        assert result.exit_code == 1
        assert "No tasks found" in result.output

    def test_empty_file_with_allow_empty_exits_0(self, tmp_path: Path):
        """Empty tasks file with --allow-empty should exit with code 0."""
        empty_file = tmp_path / "empty-tasks.md"
        empty_file.write_text("")

        result = runner.invoke(app, ["tasks", str(empty_file), "--allow-empty"])

        assert result.exit_code == 0

    def test_malformed_tasks_exits_1(self, tmp_path: Path):
        """Tasks file with no parseable tasks should exit with code 1."""
        malformed_file = tmp_path / "malformed-tasks.md"
        malformed_file.write_text("""# Tasks: Test Feature

## Phase 1: Setup

- This is not a valid task line
- Neither is this one
- BAD_ID This won't parse either
""")

        result = runner.invoke(app, ["tasks", str(malformed_file)])

        assert result.exit_code == 1
        assert "No tasks found" in result.output

    def test_valid_tasks_exits_0(self, tasks_simple_path: Path):
        """Valid tasks file should exit with code 0."""
        result = runner.invoke(app, ["tasks", str(tasks_simple_path)])

        assert result.exit_code == 0
        assert "Converted 9 tasks" in result.output


class TestSpecEmptyHandling:
    """Tests for empty file handling in spec command."""

    def test_empty_file_exits_1(self, tmp_path: Path):
        """Empty spec file should exit with code 1."""
        empty_file = tmp_path / "empty-spec.md"
        empty_file.write_text("")

        result = runner.invoke(app, ["spec", str(empty_file)])

        assert result.exit_code == 1
        assert "No user stories found" in result.output

    def test_empty_file_with_allow_empty_exits_0(self, tmp_path: Path):
        """Empty spec file with --allow-empty should exit with code 0."""
        empty_file = tmp_path / "empty-spec.md"
        empty_file.write_text("")

        result = runner.invoke(app, ["spec", str(empty_file), "--allow-empty"])

        assert result.exit_code == 0

    def test_valid_spec_exits_0(self, spec_simple_path: Path):
        """Valid spec file should exit with code 0."""
        result = runner.invoke(app, ["spec", str(spec_simple_path)])

        assert result.exit_code == 0
        assert "Converted 3 user stories" in result.output


class TestFeatureEmptyHandling:
    """Tests for empty file handling in feature command."""

    def test_no_files_exits_1(self, tmp_path: Path):
        """Directory without spec.md or tasks.md should exit with code 1."""
        result = runner.invoke(app, ["feature", str(tmp_path)])

        assert result.exit_code == 1
        assert "No spec.md or tasks.md found" in result.output

    def test_empty_files_exits_1(self, tmp_path: Path):
        """Directory with empty spec.md and tasks.md should exit with code 1."""
        (tmp_path / "spec.md").write_text("")
        (tmp_path / "tasks.md").write_text("")

        result = runner.invoke(app, ["feature", str(tmp_path)])

        assert result.exit_code == 1
        assert "No issues found" in result.output

    def test_empty_files_with_allow_empty_exits_0(self, tmp_path: Path):
        """Empty files with --allow-empty should exit with code 0."""
        (tmp_path / "spec.md").write_text("")
        (tmp_path / "tasks.md").write_text("")

        result = runner.invoke(app, ["feature", str(tmp_path), "--allow-empty"])

        assert result.exit_code == 0


class TestImportEmptyHandling:
    """Tests for empty file handling in import command."""

    def test_empty_tasks_exits_1(self, tmp_path: Path):
        """Empty tasks file should exit with code 1."""
        empty_file = tmp_path / "empty-tasks.md"
        empty_file.write_text("")

        result = runner.invoke(app, ["import", str(empty_file), "--dry-run"])

        assert result.exit_code == 1
        assert "No items found" in result.output

    def test_empty_tasks_with_allow_empty_exits_0(self, tmp_path: Path):
        """Empty tasks file with --allow-empty should exit with code 0."""
        empty_file = tmp_path / "empty-tasks.md"
        empty_file.write_text("")

        result = runner.invoke(app, ["import", str(empty_file), "--dry-run", "--allow-empty"])

        assert result.exit_code == 0

    def test_empty_spec_exits_1(self, tmp_path: Path):
        """Empty spec file should exit with code 1."""
        empty_file = tmp_path / "empty-spec.md"
        empty_file.write_text("")

        result = runner.invoke(app, ["import", str(empty_file), "--dry-run"])

        assert result.exit_code == 1
        assert "No items found" in result.output


class TestVerboseWithEmpty:
    """Tests for verbose output with empty files."""

    def test_verbose_shows_parsing_info_before_error(self, tmp_path: Path):
        """Verbose mode should show parsing info even when failing."""
        empty_file = tmp_path / "empty-tasks.md"
        empty_file.write_text("")

        result = runner.invoke(app, ["--verbose", "tasks", str(empty_file)])

        assert result.exit_code == 1
        assert "Parsed 0 phases with 0 tasks" in result.output
        assert "No tasks found" in result.output
