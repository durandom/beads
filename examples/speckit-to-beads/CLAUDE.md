# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is **speckit-to-beads**, a CLI tool that converts [spec-kit](https://github.com/github/spec-kit) Markdown output (`tasks.md`, `spec.md`) to [beads](https://github.com/steveyegge/beads) JSONL format for import into the `bd` issue tracker.

## Commands

```bash
# Install for development (requires Python 3.11+)
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run a single test
pytest tests/test_parsers.py::TestParseTaskLine::test_simple_task -v

# Type check
mypy src/

# Lint
ruff check src/

# CLI usage
speckit-to-beads tasks path/to/tasks.md        # Convert tasks to JSONL (stdout)
speckit-to-beads spec path/to/spec.md          # Convert spec to JSONL (stdout)
speckit-to-beads feature path/to/feature-dir/  # Convert both if present
speckit-to-beads tasks path/to/tasks.md --dry-run  # Preview without output
speckit-to-beads tasks path/to/tasks.md --epic bd-42  # Link tasks to parent epic
```

## Architecture

```
src/speckit_to_beads/
├── models.py      # Pydantic models: Input (SpecKit*) → Output (Beads*)
├── parsers.py     # Regex-based parsers for tasks.md and spec.md
├── converter.py   # Transform SpecKit models → BeadsIssue list → JSONL
└── cli.py         # Typer CLI with tasks/spec/feature subcommands
```

**Data flow**: `Markdown file → parse_*_file() → SpecKit* models → *_to_beads() → BeadsIssue list → to_jsonl() → stdout`

The output is piped directly to `bd import` for ingestion into the beads issue tracker.

## Spec-Kit → Beads Mapping

| Spec-Kit Element | Beads Representation |
|------------------|----------------------|
| Task ID `T001` | Label `speckit:T001` |
| `[P]` marker | Label `parallel` |
| `[US1]` marker | Label `US1` |
| Phase number | Label `phase:N` |
| `(depends on T012)` | Dependency with `type: "blocks"` |
| User story `US1` | Issue with `type: "feature"` |
| Task | Issue with `type: "task"` |
| `--epic bd-42` | Dependency with `type: "parent-child"` |

## Test Fixtures

Test fixtures live in `tests/fixtures/`:
- `tasks-simple.md` - Basic tasks.md with phases and markers
- `tasks-full.md` - Complex tasks.md with all features (dependencies, file paths)
- `spec-simple.md` - Spec with user stories, requirements, success criteria
