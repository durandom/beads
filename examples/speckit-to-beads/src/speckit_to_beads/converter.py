"""Convert spec-kit parsed models to beads issues.

Two conversion modes:
1. JSONL mode (to_jsonl): For batch import, dependencies use speckit IDs
2. CLI mode (import_*): Uses bd create + bd dep add with proper ID resolution

The CLI mode is recommended as it:
- Resolves dependencies correctly (T001 → bd-xxx mapping)
- Supports idempotency via --external-ref
- Provides real-time error feedback
"""

import json
from dataclasses import dataclass, field
from typing import Callable, Optional

from .bd_client import BdClient, BdError, CreatedIssue
from .models import (
    SpecKitTask,
    SpecKitTasksFile,
    SpecKitUserStory,
    SpecKitSpec,
    BeadsIssue,
    BeadsDependency,
)


# =============================================================================
# Conversion Result Types
# =============================================================================


@dataclass
class ConversionResult:
    """Result of a CLI-based conversion."""

    created: list[CreatedIssue] = field(default_factory=list)
    dependencies_added: int = 0
    errors: list[str] = field(default_factory=list)
    id_map: dict[str, str] = field(default_factory=dict)  # speckit ID → beads ID

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


# =============================================================================
# CLI-Based Conversion (Recommended)
# =============================================================================


ProgressCallback = Callable[[str, str], None]  # (action, message)


def import_tasks(
    tasks_file: SpecKitTasksFile,
    client: BdClient,
    *,
    epic_id: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> ConversionResult:
    """Import tasks.md using bd CLI with proper dependency resolution.

    This is the recommended approach as it:
    - Resolves speckit IDs to beads IDs for dependencies
    - Uses external_ref for idempotency
    - Provides real-time error feedback

    Args:
        tasks_file: Parsed tasks.md file
        client: BdClient instance
        epic_id: Optional epic ID to link all tasks as children
        on_progress: Optional callback for progress reporting

    Returns:
        ConversionResult with created issues, dependencies, and any errors

    Pattern:
        Following WORKFLOWS.md Epic Planning:
        1. Create all issues first (no dependencies)
        2. Add dependencies with resolved IDs
        This ensures all IDs exist before linking.
    """
    result = ConversionResult()

    def report(action: str, message: str) -> None:
        if on_progress:
            on_progress(action, message)

    # Phase 1: Create all issues (collect ID mapping)
    report("phase", "Creating issues...")

    for task in tasks_file.all_tasks:
        external_ref = f"speckit:{task.id}"

        # Build labels
        labels = [f"speckit:{task.id}"]
        if task.parallel:
            labels.append("parallel")
        if task.user_story:
            labels.append(task.user_story)
        if task.phase is not None:
            labels.append(f"phase:{task.phase}")

        # Build description
        description = f"File: {task.file_path}" if task.file_path else ""

        try:
            created = client.create(
                title=f"{task.id}: {task.description}",
                description=description,
                priority=2,
                issue_type="task",
                labels=labels,
                parent=epic_id,
                external_ref=external_ref,
            )
            result.created.append(created)
            result.id_map[task.id] = created.id
            report("created", f"{task.id} → {created.id}")

        except BdError as e:
            result.errors.append(f"Failed to create {task.id}: {e}")
            report("error", f"Failed to create {task.id}")

    # Phase 2: Add dependencies with resolved IDs
    report("phase", "Adding dependencies...")

    for task in tasks_file.all_tasks:
        if task.id not in result.id_map:
            continue  # Skip if creation failed

        for dep_id in task.dependencies:
            if dep_id not in result.id_map:
                result.errors.append(
                    f"{task.id} depends on {dep_id} which wasn't created"
                )
                continue

            try:
                # "X needs Y" → bd dep add X Y
                # task.id needs dep_id → dep_id blocks task.id
                client.add_dependency(
                    from_id=result.id_map[task.id],
                    to_id=result.id_map[dep_id],
                    dep_type="blocks",
                )
                result.dependencies_added += 1
                report("dependency", f"{task.id} ← {dep_id}")

            except BdError as e:
                result.errors.append(
                    f"Failed to add dependency {task.id} ← {dep_id}: {e}"
                )

    return result


def import_spec(
    spec: SpecKitSpec,
    client: BdClient,
    *,
    epic_id: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> ConversionResult:
    """Import spec.md user stories using bd CLI.

    Args:
        spec: Parsed spec.md file
        client: BdClient instance
        epic_id: Optional epic ID to link all stories as children
        on_progress: Optional callback for progress reporting

    Returns:
        ConversionResult with created issues
    """
    result = ConversionResult()

    def report(action: str, message: str) -> None:
        if on_progress:
            on_progress(action, message)

    for story in spec.user_stories:
        external_ref = f"speckit:US{story.number}"

        # Build labels
        labels = [
            f"speckit:US{story.number}",
            f"P{story.priority}",
        ]

        # Build description
        description_parts = []
        if story.description:
            description_parts.append(story.description.strip())
        if story.why_priority:
            description_parts.append(f"\n**Why this priority**: {story.why_priority}")
        if story.independent_test:
            description_parts.append(f"\n**Independent Test**: {story.independent_test}")

        # Build acceptance criteria (goes in --design per PATTERNS.md)
        design_parts = []
        if story.acceptance_scenarios:
            design_parts.append("**Acceptance Scenarios:**")
            for scenario in story.acceptance_scenarios:
                design_parts.append(
                    f"- **Given** {scenario.given}, **When** {scenario.when}, **Then** {scenario.then}"
                )

        try:
            created = client.create(
                title=f"US{story.number}: {story.title}",
                description="\n".join(description_parts) if description_parts else "",
                design="\n".join(design_parts) if design_parts else None,
                priority=story.priority,
                issue_type="feature",
                labels=labels,
                parent=epic_id,
                external_ref=external_ref,
            )
            result.created.append(created)
            result.id_map[f"US{story.number}"] = created.id
            report("created", f"US{story.number} → {created.id}")

        except BdError as e:
            result.errors.append(f"Failed to create US{story.number}: {e}")
            report("error", f"Failed to create US{story.number}")

    return result


# =============================================================================
# JSONL-Based Conversion (Legacy, for batch import)
# =============================================================================


def task_to_bead(
    task: SpecKitTask,
    epic_id: Optional[str] = None,
) -> BeadsIssue:
    """Convert a single spec-kit task to a beads issue.

    Args:
        task: Parsed spec-kit task
        epic_id: Optional epic ID to link as parent

    Returns:
        BeadsIssue ready for JSONL export
    """
    # Build labels
    labels = [f"speckit:{task.id}"]

    if task.parallel:
        labels.append("parallel")

    if task.user_story:
        labels.append(task.user_story)

    if task.phase is not None:
        labels.append(f"phase:{task.phase}")

    # Build description with file path if present
    description_parts = []
    if task.file_path:
        description_parts.append(f"File: {task.file_path}")

    # Build dependencies
    dependencies: list[BeadsDependency] = []

    # Add blocking dependencies (spec-kit dependencies block this task)
    for dep_id in task.dependencies:
        dependencies.append(
            BeadsDependency(
                depends_on_id=dep_id,
                type="blocks",
            )
        )

    # Add parent-child dependency if epic specified
    if epic_id:
        dependencies.append(
            BeadsDependency(
                depends_on_id=epic_id,
                type="parent-child",
            )
        )

    return BeadsIssue(
        title=f"{task.id}: {task.description}",
        description="\n".join(description_parts) if description_parts else "",
        status="closed" if task.status == "closed" else "open",
        priority=2,  # Default priority, could be inferred from phase
        issue_type="task",
        labels=labels,
        dependencies=dependencies,
    )


def tasks_file_to_beads(
    tasks_file: SpecKitTasksFile,
    epic_id: Optional[str] = None,
) -> list[BeadsIssue]:
    """Convert a complete tasks.md file to beads issues.

    Args:
        tasks_file: Parsed tasks.md file
        epic_id: Optional epic ID to link all tasks as children

    Returns:
        List of BeadsIssue ready for JSONL export
    """
    beads = []

    for task in tasks_file.all_tasks:
        bead = task_to_bead(task, epic_id=epic_id)
        beads.append(bead)

    return beads


def user_story_to_bead(
    story: SpecKitUserStory,
    feature_name: str,
    epic_id: Optional[str] = None,
) -> BeadsIssue:
    """Convert a user story to a beads issue.

    Args:
        story: Parsed user story
        feature_name: Feature name for context
        epic_id: Optional epic ID to link as parent

    Returns:
        BeadsIssue with type=feature
    """
    # Build labels
    labels = [
        f"speckit:US{story.number}",
        f"P{story.priority}",
    ]

    # Build description
    description_parts = []
    if story.description:
        description_parts.append(story.description.strip())

    if story.why_priority:
        description_parts.append(f"\n**Why this priority**: {story.why_priority}")

    if story.independent_test:
        description_parts.append(f"\n**Independent Test**: {story.independent_test}")

    # Build acceptance criteria
    acceptance_parts = []
    for scenario in story.acceptance_scenarios:
        acceptance_parts.append(
            f"- **Given** {scenario.given}, **When** {scenario.when}, **Then** {scenario.then}"
        )
    acceptance_criteria = "\n".join(acceptance_parts) if acceptance_parts else None

    # Build dependencies
    dependencies: list[BeadsDependency] = []
    if epic_id:
        dependencies.append(
            BeadsDependency(
                depends_on_id=epic_id,
                type="parent-child",
            )
        )

    return BeadsIssue(
        title=f"US{story.number}: {story.title}",
        description="\n".join(description_parts) if description_parts else "",
        acceptance_criteria=acceptance_criteria,
        status="open",
        priority=story.priority,
        issue_type="feature",
        labels=labels,
        dependencies=dependencies,
    )


def spec_file_to_beads(
    spec: SpecKitSpec,
    epic_id: Optional[str] = None,
) -> list[BeadsIssue]:
    """Convert a complete spec.md file to beads issues.

    Args:
        spec: Parsed spec.md file
        epic_id: Optional epic ID to link all stories as children

    Returns:
        List of BeadsIssue (user stories as features)
    """
    beads = []

    for story in spec.user_stories:
        bead = user_story_to_bead(story, spec.feature_name, epic_id=epic_id)
        beads.append(bead)

    return beads


def to_jsonl(beads: list[BeadsIssue]) -> str:
    """Convert beads issues to JSONL format.

    Args:
        beads: List of BeadsIssue to convert

    Returns:
        JSONL string (one JSON object per line)
    """
    lines = []
    for bead in beads:
        data = bead.model_dump_jsonl()
        lines.append(json.dumps(data, ensure_ascii=False))
    return "\n".join(lines)
