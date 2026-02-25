"""Client for interacting with bd CLI.

Follows patterns from examples/python-agent/agent.py and integrations/beads-mcp/.
"""

import json
import subprocess
from dataclasses import dataclass
from typing import Any


class BdError(Exception):
    """Error from bd CLI command."""

    def __init__(self, command: list[str], stderr: str, returncode: int):
        self.command = command
        self.stderr = stderr
        self.returncode = returncode
        cmd_str = " ".join(command)
        super().__init__(f"bd command failed: {cmd_str}\nError: {stderr}")


@dataclass
class CreatedIssue:
    """Result from bd create."""

    id: str
    title: str
    external_ref: str | None = None


@dataclass
class DependencyAdded:
    """Result from bd dep add."""

    from_id: str
    to_id: str
    dep_type: str


class BdClient:
    """Client for bd CLI commands.

    Uses subprocess + JSON output for reliable parsing.
    Follows the pattern from beads-mcp/bd_client.py.
    """

    def __init__(self, bd_path: str = "bd", dry_run: bool = False):
        """Initialize client.

        Args:
            bd_path: Path to bd binary (default: "bd" from PATH)
            dry_run: If True, don't execute commands, just return mock data
        """
        self.bd_path = bd_path
        self.dry_run = dry_run
        self._dry_run_counter = 0

    def _run(self, args: list[str], expect_json: bool = True) -> Any:
        """Run bd command and return result.

        Args:
            args: Command arguments (without "bd" prefix)
            expect_json: If True, parse output as JSON

        Returns:
            Parsed JSON (dict or list) or raw string output

        Raises:
            BdError: If command fails
        """
        cmd = [self.bd_path] + args
        if expect_json and "--json" not in args:
            cmd.append("--json")

        if self.dry_run:
            return self._mock_response(args)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise BdError(cmd, result.stderr.strip(), result.returncode)

        if expect_json and result.stdout.strip():
            return json.loads(result.stdout)
        return result.stdout

    def _mock_response(self, args: list[str]) -> Any:
        """Generate mock response for dry-run mode."""
        self._dry_run_counter += 1

        if args[0] == "create":
            # Extract title from args
            title = args[1] if len(args) > 1 else "Unknown"
            return {
                "id": f"dry-{self._dry_run_counter}",
                "title": title,
                "status": "open",
            }
        elif args[0] == "dep":
            return {"success": True}
        elif args[0] == "list":
            return []
        else:
            return {}

    def create(
        self,
        title: str,
        *,
        description: str | None = None,
        design: str | None = None,
        acceptance: str | None = None,
        notes: str | None = None,
        priority: int = 2,
        issue_type: str = "task",
        labels: list[str] | None = None,
        parent: str | None = None,
        external_ref: str | None = None,
    ) -> CreatedIssue:
        """Create a new issue.

        Args:
            title: Issue title
            description: Issue description
            design: Design notes (planning decisions)
            acceptance: Acceptance criteria
            notes: Progress notes
            priority: Priority 0-4 (default 2)
            issue_type: bug|feature|task|epic|chore (default task)
            labels: Labels to add
            parent: Parent issue ID for hierarchical linking
            external_ref: External reference for idempotency (e.g., "speckit:T001")

        Returns:
            CreatedIssue with the created issue's ID

        Raises:
            BdError: If creation fails
        """
        args = ["create", title]

        if description:
            args.extend(["--description", description])
        if design:
            args.extend(["--design", design])
        if acceptance:
            args.extend(["--acceptance", acceptance])
        if notes:
            args.extend(["--notes", notes])

        args.extend(["--priority", str(priority)])
        args.extend(["--type", issue_type])

        if labels:
            args.extend(["--labels", ",".join(labels)])
        if parent:
            args.extend(["--parent", parent])
        if external_ref:
            args.extend(["--external-ref", external_ref])

        result = self._run(args)
        assert isinstance(result, dict)

        return CreatedIssue(
            id=result["id"],
            title=result.get("title", title),
            external_ref=external_ref,
        )

    def add_dependency(
        self,
        from_id: str,
        to_id: str,
        dep_type: str = "blocks",
    ) -> DependencyAdded:
        """Add a dependency between issues.

        Args:
            from_id: Issue that depends on another (the blocked one)
            to_id: Issue that blocks the first (the blocker)
            dep_type: blocks|related|parent-child|discovered-from

        Returns:
            DependencyAdded confirmation

        Note:
            "X needs Y" → add_dependency(X, Y) → Y blocks X
            This matches the Ready Front pattern from WORKFLOWS.md
        """
        args = ["dep", "add", from_id, to_id, "--type", dep_type]
        self._run(args, expect_json=False)

        return DependencyAdded(
            from_id=from_id,
            to_id=to_id,
            dep_type=dep_type,
        )

    def find_by_external_ref(self, external_ref: str) -> str | None:
        """Find issue by external reference.

        Args:
            external_ref: External reference to search for

        Returns:
            Issue ID if found, None otherwise

        Used for idempotency checking before creation.
        """
        try:
            result = self._run(["list", "--external-ref", external_ref])
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("id")
        except BdError:
            pass
        return None

    def check_available(self) -> bool:
        """Check if bd is available and working.

        Returns:
            True if bd is available
        """
        try:
            result = subprocess.run(
                [self.bd_path, "--version"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
