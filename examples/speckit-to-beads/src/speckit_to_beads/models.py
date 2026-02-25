"""Pydantic models for spec-kit artifacts and beads output."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# Input Models: Spec-Kit Artifacts
# =============================================================================


class SpecKitTask(BaseModel):
    """Parsed task from tasks.md.

    Example input:
        - [ ] T014 [P] [US1] Implement AuthService in src/services/auth.py (depends on T012, T013)
    """

    id: str = Field(description="Task ID, e.g., T001, T014")
    status: Literal["open", "closed"] = Field(default="open")
    parallel: bool = Field(default=False, description="[P] marker present")
    user_story: str | None = Field(default=None, description="User story, e.g., US1, US2")
    description: str = Field(description="Task description text")
    file_path: str | None = Field(default=None, description="File path from 'in path/to/file'")
    dependencies: list[str] = Field(
        default_factory=list, description="Dependencies, e.g., ['T012', 'T013']"
    )
    phase: int | None = Field(default=None, description="Phase number from parent heading")
    phase_title: str | None = Field(default=None, description="Phase title")


class SpecKitPhase(BaseModel):
    """Parsed phase from tasks.md.

    Example input:
        ## Phase 1: Setup (Shared Infrastructure)

        **Purpose**: Project initialization and basic structure

        - [ ] T001 Create project structure
    """

    number: int = Field(description="Phase number")
    title: str = Field(description="Phase title, e.g., 'Setup'")
    subtitle: str | None = Field(default=None, description="Subtitle in parentheses")
    purpose: str | None = Field(default=None, description="Purpose from **Purpose**: line")
    checkpoint: str | None = Field(default=None, description="Checkpoint text")
    tasks: list[SpecKitTask] = Field(default_factory=list)


class SpecKitTasksFile(BaseModel):
    """Complete parsed tasks.md file."""

    feature_name: str | None = Field(default=None, description="From # Tasks: [name]")
    phases: list[SpecKitPhase] = Field(default_factory=list)

    @property
    def all_tasks(self) -> list[SpecKitTask]:
        """Flatten all tasks from all phases."""
        return [task for phase in self.phases for task in phase.tasks]


class AcceptanceScenario(BaseModel):
    """Given/When/Then acceptance scenario."""

    given: str
    when: str
    then: str


class SpecKitUserStory(BaseModel):
    """Parsed user story from spec.md.

    Example input:
        ### User Story 1 - Login Flow (Priority: P1)

        User can log in with email and password.

        **Acceptance Scenarios**:
        1. **Given** unauthenticated user, **When** valid credentials, **Then** session created
    """

    number: int = Field(description="Story number, e.g., 1, 2, 3")
    title: str = Field(description="Story title")
    priority: int = Field(description="Priority as int, P1 → 1, P2 → 2")
    description: str = Field(default="")
    why_priority: str | None = Field(default=None)
    independent_test: str | None = Field(default=None)
    acceptance_scenarios: list[AcceptanceScenario] = Field(default_factory=list)


class SpecKitRequirement(BaseModel):
    """Functional requirement from spec.md."""

    id: str = Field(description="Requirement ID, e.g., FR-001")
    text: str = Field(description="Requirement text")
    needs_clarification: str | None = Field(default=None)


class SpecKitSuccessCriterion(BaseModel):
    """Success criterion from spec.md."""

    id: str = Field(description="Success criterion ID, e.g., SC-001")
    text: str = Field(description="Criterion text")


class SpecKitSpec(BaseModel):
    """Complete parsed spec.md file."""

    feature_name: str
    feature_branch: str | None = Field(default=None, description="e.g., 001-user-auth")
    created: str | None = Field(default=None)
    status: str | None = Field(default=None)
    user_stories: list[SpecKitUserStory] = Field(default_factory=list)
    requirements: list[SpecKitRequirement] = Field(default_factory=list)
    success_criteria: list[SpecKitSuccessCriterion] = Field(default_factory=list)


# =============================================================================
# Output Models: Beads-Compatible JSONL
# =============================================================================


class BeadsDependency(BaseModel):
    """Dependency in beads JSONL format."""

    issue_id: str = Field(default="", description="Will be set by beads import")
    depends_on_id: str
    type: Literal["blocks", "related", "parent-child", "discovered-from"] = "blocks"


class BeadsIssue(BaseModel):
    """Issue in beads JSONL format for bd import."""

    id: str | None = Field(default=None, description="Optional explicit ID")
    title: str
    description: str = ""
    status: Literal["open", "in_progress", "blocked", "deferred", "closed"] = "open"
    priority: int = Field(default=2, ge=0, le=4)
    issue_type: Literal["bug", "feature", "task", "epic", "chore"] = "task"
    labels: list[str] = Field(default_factory=list)
    dependencies: list[BeadsDependency] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    # Optional fields
    assignee: str | None = None
    design: str | None = None
    acceptance_criteria: str | None = None
    notes: str | None = None
    external_ref: str | None = None

    def model_dump_jsonl(self) -> dict:
        """Dump for JSONL output, excluding None values and empty lists."""
        data = self.model_dump(exclude_none=True)
        # Remove empty lists for cleaner output
        if not data.get("labels"):
            data.pop("labels", None)
        if not data.get("dependencies"):
            data.pop("dependencies", None)
        return data
