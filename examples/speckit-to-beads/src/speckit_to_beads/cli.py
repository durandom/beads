"""CLI for converting spec-kit files to beads issues.

Two modes:
1. JSONL mode (tasks, spec, feature commands): Output JSONL to stdout, pipe to bd import
2. CLI mode (import command): Direct bd create + bd dep add with proper ID resolution

CLI mode is recommended for proper dependency resolution and idempotency.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .bd_client import BdClient
from .converter import (
    tasks_file_to_beads,
    spec_file_to_beads,
    to_jsonl,
    import_tasks,
    import_spec,
    ConversionResult,
)
from .parsers import parse_tasks_file, parse_spec_file

app = typer.Typer(
    name="speckit-to-beads",
    help="Convert spec-kit output files to beads issues.",
    add_completion=False,
)
console = Console(stderr=True)
verbose: bool = False


def vprint(msg: str) -> None:
    """Print message if verbose mode is enabled."""
    if verbose:
        console.print(f"[dim]{msg}[/dim]")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"speckit-to-beads v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    verbose_opt: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed parsing and conversion info.",
    ),
) -> None:
    """Convert spec-kit output files to beads JSONL format."""
    global verbose
    verbose = verbose_opt


@app.command()
def tasks(
    tasks_file: Path = typer.Argument(
        ...,
        help="Path to tasks.md file",
        exists=True,
        dir_okay=False,
    ),
    epic: Optional[str] = typer.Option(
        None,
        "--epic",
        "-e",
        help="Epic ID to link all tasks as children (e.g., bd-42)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview conversion without outputting JSONL",
    ),
    allow_empty: bool = typer.Option(
        False,
        "--allow-empty",
        help="Exit 0 even if no tasks found (default: exit 1 on empty)",
    ),
) -> None:
    """Convert tasks.md to beads JSONL.

    Output is written to stdout. Pipe to `bd import` for direct import:

        speckit-to-beads tasks path/to/tasks.md | bd import
    """
    content = tasks_file.read_text()
    parsed = parse_tasks_file(content)

    # Verbose: show parsing results
    vprint(f"Parsed {len(parsed.phases)} phases with {len(parsed.all_tasks)} tasks")
    for phase in parsed.phases:
        deps = sum(1 for t in phase.tasks if t.dependencies)
        parallel = sum(1 for t in phase.tasks if t.parallel)
        extras = []
        if deps:
            extras.append(f"{deps} with deps")
        if parallel:
            extras.append(f"{parallel} parallel")
        extra_str = f" ({', '.join(extras)})" if extras else ""
        vprint(f"  Phase {phase.number}: {len(phase.tasks)} tasks{extra_str}")

    if dry_run:
        console.print(
            Panel(
                f"[bold]Feature:[/bold] {parsed.feature_name or 'Unknown'}\n"
                f"[bold]Phases:[/bold] {len(parsed.phases)}\n"
                f"[bold]Tasks:[/bold] {len(parsed.all_tasks)}",
                title="Dry Run Preview",
            )
        )

        for phase in parsed.phases:
            console.print(f"\n[bold cyan]Phase {phase.number}: {phase.title}[/bold cyan]")
            for task in phase.tasks:
                status_icon = "✓" if task.status == "closed" else "○"
                markers = []
                if task.parallel:
                    markers.append("[P]")
                if task.user_story:
                    markers.append(f"[{task.user_story}]")
                marker_str = " ".join(markers) + " " if markers else ""
                console.print(f"  {status_icon} {task.id} {marker_str}{task.description}")

        if epic:
            console.print(f"\n[dim]All tasks will be linked to epic: {epic}[/dim]")

        return

    # Convert and output
    beads = tasks_file_to_beads(parsed, epic_id=epic)

    if not beads and not allow_empty:
        console.print("[red]Error: No tasks found. Check file format.[/red]")
        raise typer.Exit(1)

    jsonl = to_jsonl(beads)
    print(jsonl)

    console.print(f"[green]✓ Converted {len(beads)} tasks to JSONL[/green]")


@app.command()
def spec(
    spec_file: Path = typer.Argument(
        ...,
        help="Path to spec.md file",
        exists=True,
        dir_okay=False,
    ),
    epic: Optional[str] = typer.Option(
        None,
        "--epic",
        "-e",
        help="Epic ID to link all stories as children",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview conversion without outputting JSONL",
    ),
    allow_empty: bool = typer.Option(
        False,
        "--allow-empty",
        help="Exit 0 even if no user stories found (default: exit 1 on empty)",
    ),
) -> None:
    """Convert spec.md user stories to beads JSONL.

    Output is written to stdout. Pipe to `bd import` for direct import:

        speckit-to-beads spec path/to/spec.md | bd import
    """
    content = spec_file.read_text()
    parsed = parse_spec_file(content)

    # Verbose: show parsing results
    total_scenarios = sum(len(s.acceptance_scenarios) for s in parsed.user_stories)
    vprint(
        f"Parsed {len(parsed.user_stories)} user stories, "
        f"{len(parsed.requirements)} requirements, {total_scenarios} acceptance scenarios"
    )
    for story in parsed.user_stories:
        vprint(f"  US{story.number}: {story.title} (P{story.priority})")

    if dry_run:
        console.print(
            Panel(
                f"[bold]Feature:[/bold] {parsed.feature_name}\n"
                f"[bold]Branch:[/bold] {parsed.feature_branch or 'Unknown'}\n"
                f"[bold]User Stories:[/bold] {len(parsed.user_stories)}\n"
                f"[bold]Requirements:[/bold] {len(parsed.requirements)}\n"
                f"[bold]Success Criteria:[/bold] {len(parsed.success_criteria)}",
                title="Dry Run Preview",
            )
        )

        for story in parsed.user_stories:
            console.print(
                f"\n[bold cyan]US{story.number}: {story.title}[/bold cyan] (P{story.priority})"
            )
            console.print(f"  Acceptance scenarios: {len(story.acceptance_scenarios)}")

        if epic:
            console.print(f"\n[dim]All stories will be linked to epic: {epic}[/dim]")

        return

    # Convert and output
    beads = spec_file_to_beads(parsed, epic_id=epic)

    if not beads and not allow_empty:
        console.print("[red]Error: No user stories found. Check file format.[/red]")
        raise typer.Exit(1)

    jsonl = to_jsonl(beads)
    print(jsonl)

    console.print(f"[green]✓ Converted {len(beads)} user stories to JSONL[/green]")


@app.command()
def feature(
    feature_dir: Path = typer.Argument(
        ...,
        help="Path to feature directory (e.g., .specify/specs/001-feature/)",
        exists=True,
        file_okay=False,
    ),
    epic: Optional[str] = typer.Option(
        None,
        "--epic",
        "-e",
        help="Epic ID to link all issues as children",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview conversion without outputting JSONL",
    ),
    allow_empty: bool = typer.Option(
        False,
        "--allow-empty",
        help="Exit 0 even if no issues found (default: exit 1 on empty)",
    ),
) -> None:
    """Convert a complete feature directory to beads JSONL.

    Processes both spec.md and tasks.md if present.
    """
    spec_path = feature_dir / "spec.md"
    tasks_path = feature_dir / "tasks.md"

    all_beads = []

    # Process spec.md if exists
    if spec_path.exists():
        vprint("Processing spec.md...")
        spec_content = spec_path.read_text()
        spec_parsed = parse_spec_file(spec_content)
        spec_beads = spec_file_to_beads(spec_parsed, epic_id=epic)
        all_beads.extend(spec_beads)
        vprint(f"  {len(spec_parsed.user_stories)} user stories → {len(spec_beads)} issues")

        if dry_run:
            console.print(f"[bold]spec.md:[/bold] {len(spec_beads)} user stories")

    # Process tasks.md if exists
    if tasks_path.exists():
        vprint("Processing tasks.md...")
        tasks_content = tasks_path.read_text()
        tasks_parsed = parse_tasks_file(tasks_content)
        tasks_beads = tasks_file_to_beads(tasks_parsed, epic_id=epic)
        all_beads.extend(tasks_beads)
        vprint(f"  {len(tasks_parsed.all_tasks)} tasks → {len(tasks_beads)} issues")

        if dry_run:
            console.print(f"[bold]tasks.md:[/bold] {len(tasks_beads)} tasks")

    if not spec_path.exists() and not tasks_path.exists():
        console.print("[red]No spec.md or tasks.md found in directory[/red]")
        raise typer.Exit(1)

    if not all_beads and not allow_empty:
        console.print("[red]Error: No issues found. Check file format.[/red]")
        raise typer.Exit(1)

    if dry_run:
        console.print(f"\n[bold]Total:[/bold] {len(all_beads)} issues")
        if epic:
            console.print(f"[dim]All issues will be linked to epic: {epic}[/dim]")
        return

    # Output combined JSONL
    jsonl = to_jsonl(all_beads)
    print(jsonl)

    console.print(f"[green]✓ Converted {len(all_beads)} issues to JSONL[/green]")


def _report_result(result: ConversionResult) -> None:
    """Report conversion result to console."""
    if result.success:
        console.print(
            f"[green]✓ Created {len(result.created)} issues, "
            f"added {result.dependencies_added} dependencies[/green]"
        )
    else:
        console.print(f"[yellow]⚠ Created {len(result.created)} issues with errors:[/yellow]")
        for error in result.errors:
            console.print(f"  [red]• {error}[/red]")


# =============================================================================
# CLI-Based Import Commands (Recommended)
# =============================================================================


@app.command("import")
def import_command(
    file_path: Path = typer.Argument(
        ...,
        help="Path to tasks.md or spec.md file",
        exists=True,
        dir_okay=False,
    ),
    epic: Optional[str] = typer.Option(
        None,
        "--epic",
        "-e",
        help="Epic ID to link all issues as children",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview without creating issues (uses mock bd responses)",
    ),
    bd_path: str = typer.Option(
        "bd",
        "--bd-path",
        help="Path to bd binary (default: bd from PATH)",
    ),
    allow_empty: bool = typer.Option(
        False,
        "--allow-empty",
        help="Exit 0 even if no items found (default: exit 1 on empty)",
    ),
) -> None:
    """Import spec-kit file directly to beads using bd CLI.

    This is the RECOMMENDED approach as it:
    - Resolves dependencies correctly (T001 → bd-xxx mapping)
    - Uses --external-ref for idempotency (re-running won't create duplicates)
    - Provides real-time error feedback

    Examples:
        speckit-to-beads import path/to/tasks.md
        speckit-to-beads import path/to/spec.md --epic bd-42
        speckit-to-beads import path/to/tasks.md --dry-run
    """
    client = BdClient(bd_path=bd_path, dry_run=dry_run)

    # Check bd is available (unless dry-run)
    if not dry_run and not client.check_available():
        console.print("[red]Error: bd command not found. Install beads first.[/red]")
        raise typer.Exit(1)

    content = file_path.read_text()
    filename = file_path.name.lower()

    vprint(f"Detected file: {filename}")
    vprint(f"Using bd at: {bd_path}")

    # Detect file type and parse
    if "task" in filename or filename == "tasks.md":
        parsed = parse_tasks_file(content)
        console.print(
            f"[bold]Importing:[/bold] {len(parsed.all_tasks)} tasks from {file_path.name}"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Importing...", total=None)

            def on_progress(action: str, message: str) -> None:
                progress.update(task, description=f"{action}: {message}")

            result = import_tasks(parsed, client, epic_id=epic, on_progress=on_progress)

    elif "spec" in filename or filename == "spec.md":
        parsed_spec = parse_spec_file(content)
        console.print(
            f"[bold]Importing:[/bold] {len(parsed_spec.user_stories)} user stories "
            f"from {file_path.name}"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Importing...", total=None)

            def on_progress(action: str, message: str) -> None:
                progress.update(task, description=f"{action}: {message}")

            result = import_spec(parsed_spec, client, epic_id=epic, on_progress=on_progress)

    else:
        console.print(
            f"[red]Error: Cannot determine file type for {file_path.name}. "
            "Expected tasks.md or spec.md[/red]"
        )
        raise typer.Exit(1)

    if not result.created and not allow_empty:
        console.print("[red]Error: No items found. Check file format.[/red]")
        raise typer.Exit(1)

    _report_result(result)

    # Show ID mapping if dry-run or verbose
    if (dry_run or verbose) and result.id_map:
        label = "ID Mapping (dry-run)" if dry_run else "ID Mapping"
        console.print(f"\n[dim]{label}:[/dim]")
        show_all = verbose and not dry_run
        items = list(result.id_map.items()) if show_all else list(result.id_map.items())[:5]
        for speckit_id, beads_id in items:
            console.print(f"  {speckit_id} → {beads_id}")
        if not show_all and len(result.id_map) > 5:
            console.print(f"  ... and {len(result.id_map) - 5} more")

    if not result.success:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
