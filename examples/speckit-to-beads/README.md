# speckit-to-beads

Convert [spec-kit](https://github.com/github/spec-kit) output files to [beads](https://github.com/steveyegge/beads) issues.

## Installation

```bash
# With uv
uv pip install -e .

# With pip
pip install -e .
```

## Usage

### Convert tasks.md to beads JSONL

```bash
# Output to stdout
speckit-to-beads tasks path/to/tasks.md

# Pipe directly to beads
speckit-to-beads tasks path/to/tasks.md | bd import

# With epic parent
speckit-to-beads tasks path/to/tasks.md --epic bd-10
```

### Convert spec.md user stories

```bash
speckit-to-beads spec path/to/spec.md
```

### Convert full feature directory

```bash
speckit-to-beads feature path/to/.specify/specs/001-feature/
```

## Mapping

| Spec-Kit | Beads |
|----------|-------|
| `T001` | `--label "speckit:T001"` |
| `[P]` | `--label "parallel"` |
| `[US1]` | `--label "US1"` |
| `Phase N` | `--label "phase:N"` |
| `depends on T012` | dependency link |

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type check
mypy src/

# Lint
ruff check src/
```

## License

MIT
