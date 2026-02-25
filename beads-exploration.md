# Beads: A Deep Exploration

> This document captures an exploration of the beads issue tracking system, organized from foundational concepts to advanced features.

---

## Part 1: The Basics

### What is Beads?

**Beads** (`bd`) is a git-backed issue tracker designed for AI-supervised coding workflows. Issues are stored locally in SQLite and synced via JSONL files committed to git.

```
Your Code          Beads Data
    │                  │
    ├── src/           ├── .beads/beads.db (SQLite, local)
    ├── package.json   └── .beads/issues.jsonl (git-synced)
    └── README.md
```

### The Name: Beads on a String

The name comes from the metaphor of **beads on a string** — individual work items (issues) linked together by dependencies, like beads threaded on a necklace.

- `bd` (the command) sounds like "bead"
- Issues are "beads" strung together with dependencies
- The dependency chain forms the "string"

### Why Beads Over Jira/GitHub Issues?

| Problem | Jira/GitHub | Beads |
|---------|-------------|-------|
| AI context loss | Issues live in a web UI, lost after compaction | Issues live in the repo, recoverable via `bd show` |
| Dependencies | Advisory links, not enforced | `bd ready` only shows unblocked work |
| Templates | Copy-paste from old epics | `bd pour` stamps out structured workflows |
| Ephemeral work | Everything is permanent | Wisps can be burned without trace |

---

## Part 2: The Chemistry Analogy

Beads uses a **chemistry metaphor** to describe work lifecycle. This is the core conceptual framework.

### The Three Phases of Matter

```
        SOLID              LIQUID              VAPOR
        (Proto)            (Mol)               (Wisp)

     ┌──────────┐       ┌──────────┐       ┌──────────┐
     │ ❄️ Frozen │       │ 💧 Flows  │       │ 💨 Floats │
     │ Template │       │ Real Work│       │ Scratch  │
     │ Reusable │       │ Persists │       │ Ephemeral│
     └──────────┘       └──────────┘       └──────────┘
          │                   │                   │
        Git ✓              Git ✓              Git ✗
```

| Phase | Name | Storage | Git Synced | Purpose |
|-------|------|---------|------------|---------|
| Solid | **Proto** | `.beads/` | Yes | Frozen reusable template |
| Liquid | **Mol** (Molecule) | `.beads/` | Yes | Active persistent work |
| Vapor | **Wisp** | `.beads/` (ephemeral flag) | No | Throwaway operational work |

### The Vocabulary

| Chemistry Term | Beads Term | What It Is |
|----------------|------------|------------|
| Atom | Issue/Bead | Single work item |
| Molecule | Epic + children | Group of related issues with dependencies |
| Proto(n) | Template | Frozen pattern you can reuse (likely a pun on "proton") |
| Mol | Instance | Real work, flows through your pipeline |
| Wisp | Ephemeral instance | Throwaway work that evaporates |

### Phase Transitions (Commands)

```
                    ┌─────────────────┐
                    │  PROTO (Solid)  │
                    │  Frozen template│
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                │                ▼
     ┌─────────────┐         │         ┌─────────────┐
     │ bd pour     │         │         │ bd wisp     │
     │             │         │         │ create      │
     │ MOL (Liquid)│         │         │WISP (Vapor) │
     │ Persistent  │         │         │ Ephemeral   │
     └──────┬──────┘         │         └──────┬──────┘
            │                │                │
            ▼                │         ┌──────┴──────┐
       ┌─────────┐           │         ▼             ▼
       │ bd close│           │    ┌─────────┐  ┌─────────┐
       │ (done)  │           │    │bd squash│  │ bd burn │
       └─────────┘           │    │→ digest │  │→ gone   │
                             │    └─────────┘  └─────────┘
                             │
                             ▼
                      ┌─────────────┐
                      │ bd distill  │
                      │ Extract new │
                      │ proto from  │
                      │ ad-hoc work │
                      └─────────────┘
```

| Command | Chemistry Action | What Happens |
|---------|------------------|--------------|
| `bd pour <proto>` | Melt solid → liquid | Create persistent work from template |
| `bd wisp create <proto>` | Sublime solid → vapor | Create throwaway work from template |
| `bd mol squash <id>` | Condense vapor → residue | Capture summary, discard details |
| `bd mol burn <id>` | Evaporate completely | Delete without trace |
| `bd mol distill <epic>` | Crystallize liquid → solid | Extract reusable template from ad-hoc work |

### When to Use Each Phase

| Scenario | Phase | Why |
|----------|-------|-----|
| Feature work, bug fixes | **Mol** (pour) | Needs audit trail, referenced later |
| Grooming, health checks, scratch work | **Wisp** | Operational noise, no permanent value |
| Release checklist, review template | **Proto** | Reusable pattern |

### Memory Aid

> **"Pour real work, wisp the rest, squash what's valuable, burn the rest"**

Or think of it as:
- **Proto** = Recipe book (frozen, reusable)
- **Mol** = Actual meal being cooked (real, trackable)
- **Wisp** = Taste-testing (throwaway, no one needs to know)

---

## Part 3: Issue Types and Fields

### Core Work Types

| Type | Purpose | Example |
|------|---------|---------|
| **task** | Default. Generic work item | `bd create "Fix login" -t task` |
| **bug** | Defect to fix | `bd create "Auth fails on Safari" -t bug` |
| **feature** | New functionality | `bd create "Add dark mode" -t feature` |
| **epic** | Container for child issues | `bd create "User Auth System" -t epic` |
| **chore** | Maintenance, no user value | `bd create "Update deps" -t chore` |

**Special treatment:**
- `bug` gets visual highlighting and required sections (Steps to Reproduce, Acceptance Criteria)
- `epic` enables parent-child hierarchies and becomes a "molecule" when it has children
- `task`, `feature`, `chore` are functionally equivalent for execution

### System/Infrastructure Types

| Type | Purpose |
|------|---------|
| molecule | Template for issue hierarchies (protos) |
| gate | Async coordination point (human-in-the-loop) |
| agent | Agent identity bead |
| role | Agent role definition |
| message | Ephemeral communication between workers |

These are rarely created directly — they're infrastructure for beads' workflow machinery.

### The Four Content Fields

```bash
--description        # WHAT (the problem/task)
--design             # HOW (approach, decisions, rationale)
--acceptance-criteria # DONE WHEN (verification criteria)
--notes              # RESULT (learnings, current state)
```

| Field | Purpose | Example |
|-------|---------|---------|
| `description` | WHAT needs to be done | "Add logout button to navbar" |
| `design` | HOW you'll approach it | "Using React context, not Redux" |
| `acceptance-criteria` | Success criteria | "- User sees confirmation\n- Session cleared" |
| `notes` | What actually happened | "Found auth state wasn't clearing properly" |

**Note:** `AcceptanceCriteria` is a first-class database field. "Steps to Reproduce" and "Success Criteria" are just suggested markdown headings within description.

---

## Part 4: Formulas, Protos, and Molecules

### The Layer Cake

```
Formulas (TOML/JSON files)           ← SOURCE (optional)
    ↓
Protos (issues with "template" label) ← COMPILED
    ↓
Molecules (bond, squash, burn)        ← RUNTIME
    ↓
Epics (parent-child, dependencies)    ← DATA PLANE
    ↓
Issues (JSONL, git-backed)            ← STORAGE
```

### Formula vs Proto

| | **Formula** | **Proto** |
|---|-------------|-----------|
| **What** | Source file (TOML/JSON) | Database issues |
| **Where** | `.beads/formulas/*.toml` | `.beads/beads.db` + `issues.jsonl` |
| **Format** | Declarative config with composition | Just issues with template label |
| **Features** | Extends, compose, variables | Simple cloning |

**Key insight:** A proto is just an epic (with children) that has the `template` label. That's the entire distinction.

### Two Paths to Create Templates

**Path 1: Formula → Pour/Wisp**
```bash
# Formula exists in .beads/formulas/my-workflow.formula.toml
bd formula list                              # See available formulas
bd mol wisp beads-release --var version=1.0  # Instantiate from formula
```

**Path 2: Distill from Ad-hoc Work**
```bash
# Create ad-hoc epic
bd create "My Deploy" -t epic
bd create "Build" --parent <epic>
bd create "Test" --parent <epic>
# ... realize it's reusable ...

# Extract as proto (issues with template label)
bd mol distill <epic-id> --name mol-deploy
```

### What Happens When You Pour/Wisp

```bash
bd mol wisp beads-release --var version=0.44.0
```

1. **Formula Lookup** — Find `.beads/formulas/beads-release.formula.toml`
2. **Variable Substitution** — Replace `{{version}}` with `0.44.0`
3. **Issue Creation** — Create 29 issues (one epic + children)
4. **Dependency Graph** — Wire up `needs` relationships from formula
5. **Storage** — Mark as `ephemeral=true` (wisp) so not exported to JSONL

---

## Part 5: The Agent Workflow

### How Agents Use Beads

```bash
# 1. Find unblocked work
bd ready

# 2. Get full context
bd show <id>

# 3. Claim it
bd update <id> --status in_progress

# 4. Do the work, capture learnings
bd update <id> --notes "Found that X causes Y..."

# 5. Close when done
bd close <id> --reason "Implemented via commit abc123"

# 6. Persist to git (always at session end)
bd sync
```

**Repeat until `bd ready` returns nothing** — workflow complete.

### Dependencies Control Everything

```
epic-root
├── child.1 (no deps → ready)      ← parallel
├── child.2 (no deps → ready)      ← parallel
├── child.3 (needs child.1)        → blocked
└── child.4 (needs child.2, child.3) → blocked
```

**No dependency = parallel.** Only explicit `bd dep add` creates sequence.

```bash
bd dep add <B> <A>   # B depends on A (B needs A to finish first)
```

---

## Part 6: Claude Integration

### The Hook System

Beads integrates with Claude Code via hooks:

```bash
bd setup claude              # Install globally
bd setup claude --project    # Project-only
bd setup claude --check      # Verify installation
```

This configures two hooks in `~/.claude/settings.json`:

| Hook | When | What Runs | Purpose |
|------|------|-----------|---------|
| **SessionStart** | New conversation | `bd prime` | Full context injection |
| **PreCompact** | Before summarization | `bd prime --stealth` | Preserve workflow rules |

### What `bd prime` Outputs

The agent receives workflow context (~1-2k tokens):

```markdown
# Beads Workflow Context

# 🚨 SESSION CLOSE PROTOCOL 🚨
**CRITICAL**: Before saying "done", you MUST run:
[ ] 1. git status
[ ] 2. git add <files>
[ ] 3. bd sync
[ ] 4. git commit -m "..."
[ ] 5. git push

## Core Rules
- Track strategic work in beads (multi-session, dependencies)
- Use TodoWrite for simple single-session tasks
- Run `bd sync` at session end

## Essential Commands
- `bd ready` - Show issues ready to work
- `bd create --title="..." --type=task` - New issue
...
```

### The Session Close Protocol

**Important:** This is *instructions to the agent*, not automatic behavior. The agent is *told* to run these commands — nothing happens automatically.

The protocol adapts to your setup:

| Mode | Protocol | Trigger |
|------|----------|---------|
| Default | Full git workflow | Normal setup |
| Daemon auto-sync | Simplified (no `bd sync`) | `daemon.auto_commit` + `daemon.auto_push` |
| Stealth | `bd sync --flush-only` | `--stealth` flag or `no-git-ops` config |
| Local only | `bd sync --flush-only` | No git remote |

### Disabling Git Operations

```bash
# Per-session
bd setup claude --stealth

# Or permanently
bd config set no-git-ops true
```

Now the agent only sees: "Before saying done: `bd sync --flush-only`"

---

## Part 7: The Daemon

### What Is It?

The daemon is a background process (one per workspace) that handles automatic syncing.

```
┌─────────────────────────────────────────────────────────────┐
│   bd create ──► Daemon ──► Auto-flush (5s) ──► JSONL        │
│   bd update      │                                           │
│   bd close       ├──► Auto-commit ──► Git                    │
│                  └──► Auto-push ──► Remote                   │
│                                                              │
│   Socket: .beads/bd.sock                                     │
└─────────────────────────────────────────────────────────────┘
```

### The Three Auto-Sync Features

| Feature | What It Does | Config |
|---------|--------------|--------|
| Auto-flush | Export DB → JSONL (5s debounce) | Always on |
| Auto-commit | Commit JSONL to git | `daemon.auto_commit` |
| Auto-push | Push to remote | `daemon.auto_push` |

### Sync Branch (Recommended for Teams)

```bash
bd init --branch beads-sync
# or
bd config set sync.branch beads-sync
```

This creates a **dedicated branch** for beads data:

```
main (your code)
    └── beads-sync (just .beads/issues.jsonl)
```

**Benefits:**
- Beads commits don't pollute your feature branch
- Auto-commit/push runs freely without touching code
- When daemon has auto-commit + auto-push, `bd prime` tells agent to skip `bd sync`

### Checking Daemon Status

```bash
bd info
# Shows: AutoCommit, AutoPush, AutoPull status

bd daemon list
# Shows all running daemons
```

---

## Part 8: Planning Philosophy

### Beads vs Markdown Files

Beads argues: **put planning in issues, not scattered files**.

| Content | Storage | Why |
|---------|---------|-----|
| Design decisions | `--design` field | Searchable, survives compaction |
| Trade-offs / rationale | `--design` field | Explains "why" when you resume |
| What actually happened | `--notes` field | Reality vs plan |
| Success criteria | `--ac` field | Stable definition of done |
| Permanent docs (README, API) | Root `.md` files | Not issue-specific |

### The Three-Field Pattern

```bash
# WHAT / HOW / RESULT

bd create "Implement caching" -t feature \
  --description "Add caching layer to reduce API latency" \
  --design "Options evaluated:
- Redis: Good for HA, has TTL
- In-memory: Fast but volatile
Decision: Redis for TTL + cluster support" \
  --ac "- API p95 latency < 100ms
- Cache hit rate > 80%"

# Later, as you learn:
bd update cache-1 --notes "COMPLETED: Redis client setup
DISCOVERED: Need pub/sub for multi-node invalidation"
```

### Why Structure Matters

1. **Survives compaction** — `bd show <id>` recovers full context
2. **Searchable** — `bd list --design-contains "Redis"`
3. **Linked to work** — Design decisions are attached to issues, not orphaned files
4. **Evolves naturally** — Update fields as you learn

### When Markdown Files Still Make Sense

| Scenario | Use |
|----------|-----|
| Permanent API docs | `docs/API.md` |
| README / onboarding | `README.md` |
| Architecture overview (stable) | `docs/ARCHITECTURE.md` |
| Very large design (>10KB) | `history/design-x.md` + link in `--design` |

**Rule:** If it's about a *specific piece of work*, it goes in beads. If it's *permanent project documentation*, it's a file.

---

## Quick Reference

### Essential Commands

```bash
# Finding work
bd ready                           # Show unblocked work
bd list --status=open              # All open issues
bd show <id>                       # Full issue details

# Creating & updating
bd create "Title" -t task -p 2     # New issue
bd update <id> --status in_progress
bd close <id> --reason "Done"

# Dependencies
bd dep add <B> <A>                 # B depends on A
bd blocked                         # Show blocked issues

# Sync
bd sync                            # Sync with git
bd sync --flush-only               # Just export to JSONL

# Molecules
bd formula list                    # List templates
bd mol wisp <proto> --var k=v      # Create ephemeral instance
bd mol pour <proto>                # Create persistent instance
bd mol squash <id>                 # Condense to digest
bd mol burn <id>                   # Delete without trace
```

### Decision Tree: When to Use What

```
Will this work be referenced later?
│
├─ YES → Does it need audit trail / git history?
│        ├─ YES → MOL (bd pour)
│        └─ NO  → WISP (then squash if valuable)
│
└─ NO  → WISP (bd wisp create)
         End: burn (no value) or squash (capture learnings)
```

### Key File Locations

| File | Purpose |
|------|---------|
| `.beads/beads.db` | SQLite database (local) |
| `.beads/issues.jsonl` | Git-synced issue data |
| `.beads/formulas/*.toml` | Formula definitions |
| `.beads/config.yaml` | Project configuration |
| `~/.claude/settings.json` | Claude hooks configuration |

---

## Summary

Beads is **memory for AI agents** — a structured, git-backed issue tracker that:

1. **Survives context loss** — Issues persist across sessions and compaction
2. **Enforces dependencies** — `bd ready` only shows unblocked work
3. **Enables templates** — Pour/wisp reusable workflow patterns
4. **Supports ephemeral work** — Wisps for operational noise that can be burned
5. **Integrates with agents** — Hooks inject workflow context into Claude sessions

The chemistry metaphor (proto/mol/wisp, pour/distill/burn/squash) provides intuitive naming for work lifecycle management, solving the problem of database bloat from routine operations while maintaining structure during execution.
