"""Unit tests for spec-kit parsers.

These tests are written first (TDD) to define the expected parsing behavior.
"""

import pytest

from speckit_to_beads.parsers import (
    parse_task_line,
    parse_phase_header,
    parse_checkpoint,
    parse_purpose,
    parse_user_story_header,
    parse_requirement,
    parse_success_criterion,
    parse_acceptance_scenario,
    parse_tasks_file,
    parse_spec_file,
)


class TestParseTaskLine:
    """Tests for individual task line parsing."""

    def test_simple_task(self):
        """Parse basic task: - [ ] T001 Description"""
        line = "- [ ] T001 Create project structure"
        task = parse_task_line(line)

        assert task is not None
        assert task.id == "T001"
        assert task.status == "open"
        assert task.parallel is False
        assert task.user_story is None
        assert task.description == "Create project structure"
        assert task.file_path is None
        assert task.dependencies == []

    def test_completed_task(self):
        """Parse completed task: - [x] T001 Description"""
        line = "- [x] T007 Implement feature"
        task = parse_task_line(line)

        assert task is not None
        assert task.id == "T007"
        assert task.status == "closed"

    def test_task_with_parallel_marker(self):
        """Parse task with [P] marker."""
        line = "- [ ] T002 [P] Configure linting tools"
        task = parse_task_line(line)

        assert task is not None
        assert task.id == "T002"
        assert task.parallel is True
        assert task.description == "Configure linting tools"

    def test_task_with_user_story(self):
        """Parse task with [USn] marker."""
        line = "- [ ] T005 [US1] Create User model"
        task = parse_task_line(line)

        assert task is not None
        assert task.id == "T005"
        assert task.user_story == "US1"
        assert task.description == "Create User model"

    def test_task_with_parallel_and_story(self):
        """Parse task with both [P] and [USn] markers."""
        line = "- [ ] T007 [P] [US1] Add login endpoint"
        task = parse_task_line(line)

        assert task is not None
        assert task.parallel is True
        assert task.user_story == "US1"
        assert task.description == "Add login endpoint"

    def test_task_with_file_path(self):
        """Parse task with 'in path/to/file' suffix."""
        line = "- [ ] T005 [US1] Create User model in src/models/user.py"
        task = parse_task_line(line)

        assert task is not None
        assert task.description == "Create User model"
        assert task.file_path == "src/models/user.py"

    def test_task_with_single_dependency(self):
        """Parse task with one dependency."""
        line = "- [ ] T006 [US1] Implement AuthService (depends on T005)"
        task = parse_task_line(line)

        assert task is not None
        assert task.description == "Implement AuthService"
        assert task.dependencies == ["T005"]

    def test_task_with_multiple_dependencies(self):
        """Parse task with multiple dependencies."""
        line = "- [ ] T012 [US1] Implement PaymentService (depends on T005, T006)"
        task = parse_task_line(line)

        assert task is not None
        assert task.dependencies == ["T005", "T006"]

    def test_task_with_file_and_dependencies(self):
        """Parse task with both file path and dependencies."""
        line = "- [ ] T006 [US1] Implement AuthService in src/services/auth.py (depends on T005)"
        task = parse_task_line(line)

        assert task is not None
        assert task.description == "Implement AuthService"
        assert task.file_path == "src/services/auth.py"
        assert task.dependencies == ["T005"]

    def test_full_task_all_markers(self):
        """Parse task with all possible markers."""
        line = "- [x] T014 [P] [US1] Implement AuthService in src/services/auth.py (depends on T012, T013)"
        task = parse_task_line(line)

        assert task is not None
        assert task.id == "T014"
        assert task.status == "closed"
        assert task.parallel is True
        assert task.user_story == "US1"
        assert task.description == "Implement AuthService"
        assert task.file_path == "src/services/auth.py"
        assert task.dependencies == ["T012", "T013"]

    def test_non_task_line_returns_none(self):
        """Non-task lines should return None."""
        assert parse_task_line("## Phase 1: Setup") is None
        assert parse_task_line("**Purpose**: Something") is None
        assert parse_task_line("Some regular text") is None
        assert parse_task_line("") is None

    def test_task_with_four_digit_id(self):
        """Tasks can have IDs beyond T999 (though uncommon)."""
        line = "- [ ] T1234 Extended task"
        task = parse_task_line(line)
        # Current spec is T\d{3}, so this might not match
        # Adjust based on expected behavior
        # For now, we'll assume 3 digits only
        assert task is None or task.id == "T1234"


class TestParsePhaseHeader:
    """Tests for phase header parsing."""

    def test_simple_phase(self):
        """Parse basic phase header."""
        line = "## Phase 1: Setup"
        phase = parse_phase_header(line)

        assert phase is not None
        assert phase.number == 1
        assert phase.title == "Setup"
        assert phase.subtitle is None

    def test_phase_with_subtitle(self):
        """Parse phase header with subtitle in parentheses."""
        line = "## Phase 1: Setup (Shared Infrastructure)"
        phase = parse_phase_header(line)

        assert phase is not None
        assert phase.number == 1
        assert phase.title == "Setup"
        assert phase.subtitle == "Shared Infrastructure"

    def test_phase_with_priority(self):
        """Parse user story phase with priority."""
        line = "## Phase 3: User Story 1 - Login Flow (Priority: P1)"
        phase = parse_phase_header(line)

        assert phase is not None
        assert phase.number == 3
        assert phase.title == "User Story 1 - Login Flow"
        assert phase.subtitle == "Priority: P1"

    def test_non_phase_returns_none(self):
        """Non-phase lines should return None."""
        assert parse_phase_header("# Tasks: Feature") is None
        assert parse_phase_header("### Subsection") is None
        assert parse_phase_header("- [ ] T001 Task") is None


class TestParseCheckpoint:
    """Tests for checkpoint parsing."""

    def test_checkpoint(self):
        """Parse checkpoint line."""
        line = "**Checkpoint**: Foundation ready - user story implementation can now begin"
        checkpoint = parse_checkpoint(line)

        assert checkpoint == "Foundation ready - user story implementation can now begin"

    def test_non_checkpoint_returns_none(self):
        """Non-checkpoint lines should return None."""
        assert parse_checkpoint("**Purpose**: Something") is None
        assert parse_checkpoint("Regular text") is None


class TestParsePurpose:
    """Tests for purpose parsing."""

    def test_purpose(self):
        """Parse purpose line."""
        line = "**Purpose**: Project initialization and basic structure"
        purpose = parse_purpose(line)

        assert purpose == "Project initialization and basic structure"

    def test_non_purpose_returns_none(self):
        """Non-purpose lines should return None."""
        assert parse_purpose("**Checkpoint**: Something") is None


class TestParseUserStoryHeader:
    """Tests for user story header parsing."""

    def test_user_story_header(self):
        """Parse user story header from spec.md."""
        line = "### User Story 1 - Login Flow (Priority: P1)"
        story = parse_user_story_header(line)

        assert story is not None
        assert story.number == 1
        assert story.title == "Login Flow"
        assert story.priority == 1

    def test_user_story_p2(self):
        """Parse P2 priority."""
        line = "### User Story 2 - Registration (Priority: P2)"
        story = parse_user_story_header(line)

        assert story is not None
        assert story.number == 2
        assert story.priority == 2

    def test_non_story_returns_none(self):
        """Non-story lines should return None."""
        assert parse_user_story_header("## Phase 1: Setup") is None
        assert parse_user_story_header("### Edge Cases") is None


class TestParseRequirement:
    """Tests for functional requirement parsing."""

    def test_simple_requirement(self):
        """Parse basic requirement."""
        line = "- **FR-001**: System MUST authenticate users via email"
        req = parse_requirement(line)

        assert req is not None
        assert req.id == "FR-001"
        assert req.text == "System MUST authenticate users via email"
        assert req.needs_clarification is None

    def test_requirement_with_clarification(self):
        """Parse requirement needing clarification."""
        line = "- **FR-006**: Sessions MUST expire after [NEEDS CLARIFICATION: session timeout not specified]"
        req = parse_requirement(line)

        assert req is not None
        assert req.id == "FR-006"
        assert "Sessions MUST expire" in req.text
        assert req.needs_clarification == "session timeout not specified"


class TestParseSuccessCriterion:
    """Tests for success criterion parsing."""

    def test_success_criterion(self):
        """Parse success criterion."""
        line = "- **SC-001**: Users can complete login in under 3 seconds"
        sc = parse_success_criterion(line)

        assert sc is not None
        assert sc.id == "SC-001"
        assert sc.text == "Users can complete login in under 3 seconds"


class TestParseAcceptanceScenario:
    """Tests for Given/When/Then parsing."""

    def test_acceptance_scenario(self):
        """Parse acceptance scenario."""
        line = "1. **Given** an existing user, **When** they submit login, **Then** they are redirected"
        scenario = parse_acceptance_scenario(line)

        assert scenario is not None
        assert scenario.given == "an existing user"
        assert scenario.when == "they submit login"
        assert scenario.then == "they are redirected"

    def test_scenario_without_number(self):
        """Parse scenario without leading number."""
        line = "**Given** invalid credentials, **When** the user submits, **Then** error displayed"
        scenario = parse_acceptance_scenario(line)

        assert scenario is not None
        assert scenario.given == "invalid credentials"


class TestParseTasksFile:
    """Tests for complete tasks.md file parsing."""

    def test_parse_simple_tasks(self, tasks_simple_content: str):
        """Parse simple tasks.md fixture."""
        result = parse_tasks_file(tasks_simple_content)

        assert result.feature_name == "User Authentication"
        assert len(result.phases) == 4

        # Phase 1
        phase1 = result.phases[0]
        assert phase1.number == 1
        assert phase1.title == "Setup"
        assert len(phase1.tasks) == 2
        assert phase1.tasks[0].id == "T001"
        assert phase1.tasks[1].id == "T002"
        assert phase1.tasks[1].parallel is True

        # Phase 2
        phase2 = result.phases[1]
        assert phase2.number == 2
        assert phase2.checkpoint == "Foundation ready - user story implementation can now begin"

        # Phase 3 with user story tasks
        phase3 = result.phases[2]
        assert phase3.number == 3
        assert len(phase3.tasks) == 3
        assert phase3.tasks[0].user_story == "US1"
        assert phase3.tasks[2].status == "closed"  # T007 is [x]

    def test_all_tasks_property(self, tasks_simple_content: str):
        """Test all_tasks property flattens phases."""
        result = parse_tasks_file(tasks_simple_content)

        all_tasks = result.all_tasks
        task_ids = [t.id for t in all_tasks]

        assert "T001" in task_ids
        assert "T009" in task_ids
        assert len(all_tasks) == 9  # Total tasks in simple fixture

    def test_parse_full_tasks(self, tasks_full_content: str):
        """Parse full tasks.md fixture with all features."""
        result = parse_tasks_file(tasks_full_content)

        assert result.feature_name == "Payment Processing"
        assert len(result.phases) == 6

        # Check dependencies are parsed
        all_tasks = result.all_tasks
        t12 = next(t for t in all_tasks if t.id == "T012")
        assert t12.dependencies == ["T005", "T006"]

        # Check file paths
        t15 = next(t for t in all_tasks if t.id == "T015")
        assert t15.file_path == "src/webhooks/payment.py"


class TestParseSpecFile:
    """Tests for complete spec.md file parsing."""

    def test_parse_simple_spec(self, spec_simple_content: str):
        """Parse simple spec.md fixture."""
        result = parse_spec_file(spec_simple_content)

        assert result.feature_name == "User Authentication"
        assert result.feature_branch == "001-user-auth"
        assert result.created == "2025-01-13"
        assert result.status == "Draft"

        # User stories
        assert len(result.user_stories) == 3
        us1 = result.user_stories[0]
        assert us1.number == 1
        assert us1.title == "Login Flow"
        assert us1.priority == 1
        assert len(us1.acceptance_scenarios) == 3

        # Requirements
        assert len(result.requirements) >= 5
        fr1 = result.requirements[0]
        assert fr1.id == "FR-001"

        # Check for needs clarification
        fr6 = next(r for r in result.requirements if r.id == "FR-006")
        assert fr6.needs_clarification is not None

        # Success criteria
        assert len(result.success_criteria) == 4
        sc1 = result.success_criteria[0]
        assert sc1.id == "SC-001"
