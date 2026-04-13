# Beads Integration

## Overview

Beads (`br` CLI) provides an optional audit trail for task execution. Events are emitted at lifecycle boundaries — task start, complete, fail, and phase completion.

**Beads is strictly optional.** If `br` is not installed, all event emission silently no-ops. Execution never depends on beads.

## Detection

```bash
# Check if br is available
which br > /dev/null 2>&1 && echo "available" || echo "not installed"
```

## Modes

### No-DB Mode (lightweight)

Uses `.beads/issues.jsonl` as flat file storage. No Dolt database required.

```bash
# Initialize beads in no-db mode
br init --no-db

# Events stored in .beads/issues.jsonl
```

### Dolt Server Mode (full)

Uses Dolt SQL database for structured storage with branching, diffing, and querying.

```bash
# Initialize with Dolt
br init --backend dolt --database project_name

# Events stored in Dolt database tables
```

## Event Emission

### Task Started

```bash
br issue create \
  --title "T001: Add users table migration" \
  --label "in-progress" \
  --description "Phase: Register a user | Worker: backend_engineer"
```

### Task Completed

```bash
br issue update T001 \
  --status done \
  --comment "Migration applied, 2 tests passing. Files: db/migrations/002_users.py"
```

### Task Failed

```bash
br issue update T001 \
  --status blocked \
  --comment "Migration failed: duplicate column name. Retry 1/3."
```

### Task Dead (max retries exceeded)

```bash
br issue update T001 \
  --status cancelled \
  --comment "Failed after 3 retries. Last error: duplicate column name. Needs manual investigation."
```

### Phase Completed

```bash
br issue create \
  --title "Phase: Register a user" \
  --status done \
  --comment "3/3 tasks completed. PR: https://github.com/org/repo/pull/42"
```

## Export

```bash
# Export all events as JSONL for offline analysis
br events export --format jsonl > .beads/events.jsonl

# Export issues for backup
br backup --output .beads/backup.jsonl
```

## Integration Points

The `local-task-store` skill calls `emit_beads_event()` at these points:

1. **Execution start** — Creates beads issues for all tasks in the phase
2. **Task dispatch** — Updates task status to in-progress
3. **Task completion** — Updates status to done with report summary
4. **Task failure** — Updates status to blocked with error details
5. **Phase completion** — Creates phase completion record with PR link

## Configuration

Beads config lives in `.beads/config.yaml` (project-level) or `~/.beads/config.yaml` (global).

Key settings:
- `issue-prefix` — Prefix for issue IDs (auto-detected from git remote)
- `no-db` — Use JSONL flat file instead of Dolt
- `events-export` — Auto-export events to `.beads/events.jsonl`

## Remember

- Beads is fire-and-forget — never block execution on beads operations
- Wrap all `br` calls in try/catch (or check `which br` first)
- Use no-db mode for lightweight setups
- Events provide audit trail for debugging execution issues across sessions
- `.beads/` directory should be in `.gitignore`
