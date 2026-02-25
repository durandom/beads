"""Parsers for spec-kit markdown files.

This module provides regex-based parsers for:
- tasks.md: Task lists with phases, checkpoints, and dependencies
- spec.md: Feature specifications with user stories and requirements
"""

import re
from typing import Optional

from .models import (
    SpecKitTask,
    SpecKitPhase,
    SpecKitTasksFile,
    SpecKitUserStory,
    SpecKitRequirement,
    SpecKitSuccessCriterion,
    SpecKitSpec,
    AcceptanceScenario,
)


# =============================================================================
# Regex Patterns
# =============================================================================

# Task line: - [ ] T001 [P] [US1] Description in path/file.py (depends on T012, T013)
TASK_PATTERN = re.compile(
    r"^-\s+\[([ xX])\]\s+"  # Checkbox
    r"(T\d{3,4})\s+"  # Task ID (T001-T9999)
    r"(\[P\]\s+)?"  # Optional [P] marker (captured)
    r"(?:\[US(\d+)\]\s+)?"  # Optional [USn] marker
    r"(.+)$"  # Rest of line (description + file + deps)
)

# Secondary pattern to detect [P] marker
PARALLEL_PATTERN = re.compile(r"\[P\]")

# File path: "in src/path/file.py"
FILE_PATH_PATTERN = re.compile(r"\s+in\s+(\S+?)(?:\s+\(depends|\s*$)")

# Dependencies: "(depends on T012, T013)"
DEPS_PATTERN = re.compile(r"\(depends on\s+([^)]+)\)")

# Phase header: ## Phase 1: Setup (Subtitle)
PHASE_PATTERN = re.compile(
    r"^##\s+Phase\s+(\d+):\s+(.+?)(?:\s+\(([^)]+)\))?\s*$"
)

# Checkpoint: **Checkpoint**: text
CHECKPOINT_PATTERN = re.compile(r"^\*\*Checkpoint\*\*:\s+(.+)$")

# Purpose: **Purpose**: text
PURPOSE_PATTERN = re.compile(r"^\*\*Purpose\*\*:\s+(.+)$")

# User story header: ### User Story 1 - Title (Priority: P1)
USER_STORY_PATTERN = re.compile(
    r"^###\s+User Story\s+(\d+)\s+-\s+(.+?)\s+\(Priority:\s+P(\d+)\)\s*$"
)

# Functional requirement: - **FR-001**: text
REQUIREMENT_PATTERN = re.compile(r"^-\s+\*\*FR-(\d{3})\*\*:\s+(.+)$")

# Needs clarification marker
NEEDS_CLARIFICATION_PATTERN = re.compile(r"\[NEEDS CLARIFICATION:\s*([^\]]+)\]")

# Success criterion: - **SC-001**: text
SUCCESS_CRITERION_PATTERN = re.compile(r"^-\s+\*\*SC-(\d{3})\*\*:\s+(.+)$")

# Acceptance scenario: **Given** X, **When** Y, **Then** Z
ACCEPTANCE_PATTERN = re.compile(
    r"\*\*Given\*\*\s+(.+?),\s+\*\*When\*\*\s+(.+?),\s+\*\*Then\*\*\s+(.+)$"
)

# Feature name from # Tasks: [name]
TASKS_TITLE_PATTERN = re.compile(r"^#\s+Tasks:\s+(.+)$")

# Spec header patterns
SPEC_TITLE_PATTERN = re.compile(r"^#\s+Feature Specification:\s+(.+)$")
SPEC_BRANCH_PATTERN = re.compile(r"^\*\*Feature Branch\*\*:\s+`(.+)`")
SPEC_CREATED_PATTERN = re.compile(r"^\*\*Created\*\*:\s+(.+)$")
SPEC_STATUS_PATTERN = re.compile(r"^\*\*Status\*\*:\s+(.+)$")


# =============================================================================
# Line Parsers
# =============================================================================


def parse_task_line(line: str) -> Optional[SpecKitTask]:
    """Parse a single task line from tasks.md.

    Args:
        line: A line that may contain a task definition

    Returns:
        SpecKitTask if the line is a valid task, None otherwise

    Example:
        >>> parse_task_line("- [ ] T001 [P] [US1] Create model in src/models/user.py (depends on T005)")
        SpecKitTask(id='T001', parallel=True, user_story='US1', ...)
    """
    match = TASK_PATTERN.match(line.strip())
    if not match:
        return None

    checkbox, task_id, parallel_marker, user_story_num, rest = match.groups()

    # Determine status
    status = "closed" if checkbox.lower() == "x" else "open"

    # Check for [P] marker (captured in pattern)
    parallel = parallel_marker is not None

    # Extract file path
    file_path = None
    file_match = FILE_PATH_PATTERN.search(rest)
    if file_match:
        file_path = file_match.group(1)

    # Extract dependencies
    dependencies: list[str] = []
    deps_match = DEPS_PATTERN.search(rest)
    if deps_match:
        deps_str = deps_match.group(1)
        dependencies = [d.strip() for d in deps_str.split(",")]

    # Clean description: remove file path and dependencies parts
    description = rest
    # Remove "(depends on ...)" part
    description = DEPS_PATTERN.sub("", description)
    # Remove "in path/file" part
    description = re.sub(r"\s+in\s+\S+", "", description)
    description = description.strip()

    return SpecKitTask(
        id=task_id,
        status=status,
        parallel=parallel,
        user_story=f"US{user_story_num}" if user_story_num else None,
        description=description,
        file_path=file_path,
        dependencies=dependencies,
    )


def parse_phase_header(line: str) -> Optional[SpecKitPhase]:
    """Parse a phase header line.

    Args:
        line: A line that may contain a phase header

    Returns:
        SpecKitPhase (without tasks) if valid, None otherwise

    Example:
        >>> parse_phase_header("## Phase 1: Setup (Shared Infrastructure)")
        SpecKitPhase(number=1, title='Setup', subtitle='Shared Infrastructure')
    """
    match = PHASE_PATTERN.match(line.strip())
    if not match:
        return None

    number, title, subtitle = match.groups()

    return SpecKitPhase(
        number=int(number),
        title=title.strip(),
        subtitle=subtitle.strip() if subtitle else None,
    )


def parse_checkpoint(line: str) -> Optional[str]:
    """Parse a checkpoint line.

    Returns the checkpoint text or None.
    """
    match = CHECKPOINT_PATTERN.match(line.strip())
    return match.group(1) if match else None


def parse_purpose(line: str) -> Optional[str]:
    """Parse a purpose line.

    Returns the purpose text or None.
    """
    match = PURPOSE_PATTERN.match(line.strip())
    return match.group(1) if match else None


def parse_user_story_header(line: str) -> Optional[SpecKitUserStory]:
    """Parse a user story header from spec.md.

    Args:
        line: A line that may contain a user story header

    Returns:
        SpecKitUserStory (partial, without description) if valid, None otherwise

    Example:
        >>> parse_user_story_header("### User Story 1 - Login Flow (Priority: P1)")
        SpecKitUserStory(number=1, title='Login Flow', priority=1)
    """
    match = USER_STORY_PATTERN.match(line.strip())
    if not match:
        return None

    number, title, priority = match.groups()

    return SpecKitUserStory(
        number=int(number),
        title=title.strip(),
        priority=int(priority),
    )


def parse_requirement(line: str) -> Optional[SpecKitRequirement]:
    """Parse a functional requirement line.

    Example:
        >>> parse_requirement("- **FR-001**: System MUST authenticate users")
        SpecKitRequirement(id='FR-001', text='System MUST authenticate users')
    """
    match = REQUIREMENT_PATTERN.match(line.strip())
    if not match:
        return None

    req_num, text = match.groups()

    # Check for needs clarification
    clarification = None
    clarif_match = NEEDS_CLARIFICATION_PATTERN.search(text)
    if clarif_match:
        clarification = clarif_match.group(1).strip()

    return SpecKitRequirement(
        id=f"FR-{req_num}",
        text=text.strip(),
        needs_clarification=clarification,
    )


def parse_success_criterion(line: str) -> Optional[SpecKitSuccessCriterion]:
    """Parse a success criterion line.

    Example:
        >>> parse_success_criterion("- **SC-001**: Login completes in under 3 seconds")
        SpecKitSuccessCriterion(id='SC-001', text='Login completes in under 3 seconds')
    """
    match = SUCCESS_CRITERION_PATTERN.match(line.strip())
    if not match:
        return None

    sc_num, text = match.groups()

    return SpecKitSuccessCriterion(
        id=f"SC-{sc_num}",
        text=text.strip(),
    )


def parse_acceptance_scenario(line: str) -> Optional[AcceptanceScenario]:
    """Parse a Given/When/Then acceptance scenario.

    Example:
        >>> parse_acceptance_scenario("1. **Given** a user, **When** login, **Then** redirected")
        AcceptanceScenario(given='a user', when='login', then='redirected')
    """
    match = ACCEPTANCE_PATTERN.search(line.strip())
    if not match:
        return None

    given, when, then = match.groups()

    return AcceptanceScenario(
        given=given.strip(),
        when=when.strip(),
        then=then.strip(),
    )


# =============================================================================
# File Parsers
# =============================================================================


def parse_tasks_file(content: str) -> SpecKitTasksFile:
    """Parse a complete tasks.md file.

    Args:
        content: Full content of tasks.md file

    Returns:
        SpecKitTasksFile with parsed phases and tasks
    """
    result = SpecKitTasksFile()
    current_phase: Optional[SpecKitPhase] = None

    for line in content.split("\n"):
        line_stripped = line.strip()

        # Check for feature name
        title_match = TASKS_TITLE_PATTERN.match(line_stripped)
        if title_match:
            result.feature_name = title_match.group(1).strip()
            continue

        # Check for phase header
        phase = parse_phase_header(line_stripped)
        if phase:
            # Save previous phase
            if current_phase:
                result.phases.append(current_phase)
            current_phase = phase
            continue

        # If we have a current phase, parse content
        if current_phase:
            # Check for purpose
            purpose = parse_purpose(line_stripped)
            if purpose:
                current_phase.purpose = purpose
                continue

            # Check for checkpoint
            checkpoint = parse_checkpoint(line_stripped)
            if checkpoint:
                current_phase.checkpoint = checkpoint
                continue

            # Check for task
            task = parse_task_line(line_stripped)
            if task:
                task.phase = current_phase.number
                task.phase_title = current_phase.title
                current_phase.tasks.append(task)
                continue

    # Don't forget the last phase
    if current_phase:
        result.phases.append(current_phase)

    return result


def parse_spec_file(content: str) -> SpecKitSpec:
    """Parse a complete spec.md file.

    Args:
        content: Full content of spec.md file

    Returns:
        SpecKitSpec with parsed user stories, requirements, and success criteria
    """
    result = SpecKitSpec(feature_name="")
    current_story: Optional[SpecKitUserStory] = None
    current_section: Optional[str] = None
    story_content_lines: list[str] = []

    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()

        # Check for spec title
        title_match = SPEC_TITLE_PATTERN.match(line_stripped)
        if title_match:
            result.feature_name = title_match.group(1).strip()
            i += 1
            continue

        # Check for metadata
        branch_match = SPEC_BRANCH_PATTERN.match(line_stripped)
        if branch_match:
            result.feature_branch = branch_match.group(1).strip()
            i += 1
            continue

        created_match = SPEC_CREATED_PATTERN.match(line_stripped)
        if created_match:
            result.created = created_match.group(1).strip()
            i += 1
            continue

        status_match = SPEC_STATUS_PATTERN.match(line_stripped)
        if status_match:
            result.status = status_match.group(1).strip()
            i += 1
            continue

        # Check for section headers
        if line_stripped.startswith("## "):
            current_section = line_stripped[3:].strip()
            # Save current story if any
            if current_story:
                current_story.description = "\n".join(story_content_lines).strip()
                result.user_stories.append(current_story)
                current_story = None
                story_content_lines = []
            i += 1
            continue

        # Check for user story header
        story = parse_user_story_header(line_stripped)
        if story:
            # Save previous story
            if current_story:
                current_story.description = "\n".join(story_content_lines).strip()
                result.user_stories.append(current_story)
            current_story = story
            story_content_lines = []
            i += 1
            continue

        # If in a story, collect content
        if current_story:
            # Check for acceptance scenarios
            scenario = parse_acceptance_scenario(line_stripped)
            if scenario:
                current_story.acceptance_scenarios.append(scenario)
            elif line_stripped.startswith("**Why this priority**:"):
                current_story.why_priority = line_stripped.split(":", 1)[1].strip()
            elif line_stripped.startswith("**Independent Test**:"):
                current_story.independent_test = line_stripped.split(":", 1)[1].strip()
            elif not line_stripped.startswith("**Acceptance"):
                # Add to description (skip the Acceptance header itself)
                story_content_lines.append(line)

        # Check for requirements
        if current_section and "Requirements" in current_section:
            req = parse_requirement(line_stripped)
            if req:
                result.requirements.append(req)

        # Check for success criteria
        if current_section and "Success" in current_section:
            sc = parse_success_criterion(line_stripped)
            if sc:
                result.success_criteria.append(sc)

        i += 1

    # Don't forget the last story
    if current_story:
        current_story.description = "\n".join(story_content_lines).strip()
        result.user_stories.append(current_story)

    return result
