---
description: Multi-agent conductor — orchestrate multiple Claude Code instances working on issues in parallel via tmux
---

# Conduct - Multi-Agent Orchestration Command

Manage multiple Claude Code agents working on Linear issues in parallel, coordinated via file-based locks and a shared queue.

## Usage

```bash
/conduct start [--agents N] [--session NAME]   # Start conductor with N agents
/conduct status                                  # Show live dashboard
/conduct stop [--force]                          # Graceful or forced shutdown
/conduct clean                                   # Full state reset
/conduct queue list                              # Show issue queue
/conduct queue add ISSUE-1 ISSUE-2              # Add issues to queue
/conduct queue remove ISSUE-1                    # Remove from queue
```

## Overview

The conductor spawns N Claude Code instances in tmux panes, each running a work loop:
1. Sign up for a unique agent ID
2. Claim next issue from queue (own lane first, then work-steal)
3. Execute via `/execute` (or `/bug-fix`, `/chore` by label)
4. Release lock, record PR URL
5. Repeat until queue empty

Uses `dlc-conductor/conductor.sh` for process management and the `conducting` skill for orchestration logic.

## Requirements

- **tmux** — Required for multi-agent mode
- **Linear MCP** — For issue metadata and status updates
- **git gtr** — For per-issue worktree isolation (from worktrees plugin)
- **Queue populated** — Add issues before starting

## Workflow

### Step 1: Populate Queue

```bash
# Add specific issues
/conduct queue add FEAT-100 BUG-200 CHORE-50

# Check queue
/conduct queue list
```

### Step 2: Start Conductor

```bash
# Default: 3 agents
/conduct start

# Custom agent count
/conduct start --agents 5
```

This creates a tmux session with:
- **Status pane** — Live dashboard refreshing every 5 seconds
- **Agent panes** — One per agent, each running Claude Code

### Step 3: Monitor

```bash
# From any terminal
/conduct status

# Or attach to tmux
tmux attach -t dlc-conductor
```

### Step 4: Stop

```bash
# Graceful (sends Ctrl-C to agents first)
/conduct stop

# Force kill
/conduct stop --force
```

## How It Works

The command wraps `conductor.sh` (shell script) which handles:

- **Agent signup** — Atomic registration via spinlock
- **Lock management** — Per-issue file locks with TTL (default 60 min)
- **Work distribution** — Round-robin lanes + work stealing
- **Status tracking** — Aggregate dashboard from lock/done files
- **Recovery** — Expired locks auto-reclaimed, takeover for dead agents

Each spawned Claude agent executes the `conducting` skill work loop.

## State

All state lives in `.conductor/` at project root:

```
.conductor/
├── .agent-signup-sheet     # Registered agents
├── .agent-queue            # Issue queue (one ID per line)
├── .agent-done-ledger      # Completed issues (TSV)
└── issues/
    ├── FEAT-100/
    │   ├── .agent.lock     # Lock with TTL
    │   └── .agent.done     # Completion marker
    └── BUG-200/
        └── .agent.lock
```

## Examples

```bash
# Full workflow: queue issues, start 3 agents, monitor
/conduct queue add FEAT-100 FEAT-101 BUG-200 CHORE-50

/conduct start --agents 3

# Agent-1 claims FEAT-100, Agent-2 claims FEAT-101, Agent-3 claims BUG-200
# When Agent-3 finishes BUG-200, it steals CHORE-50
# When all done, agents sign off

/conduct status
# Shows: 4 total, 2 done, 1 in-progress, 1 pending

/conduct stop
/conduct clean
```

## Error Recovery

```bash
# If an agent dies, its lock expires after TTL
# Other agents auto-claim expired locks via --claim-next

# Manual recovery: transfer dead agent's work
conductor.sh --takeover agent-3 --agent agent-1

# Or let any agent grab abandoned work
conductor.sh --adopt-abandoned --agent agent-1
```

## Integration

**Requires:** tmux, Linear MCP, git gtr, conductor.sh

**Uses:** `conducting` skill (agent work loop), `execution` skill (per-issue execution), `git gtr` (worktrees)

**Subsumes:** `dlc-persistent-execute` (conductor handles retries via lock expiry)

## Remember

- Queue must be populated before starting
- Each agent gets its own tmux pane and worktree
- Locks prevent duplicate work; TTL prevents deadlocks
- Status dashboard shows real-time progress
- `.conductor/` directory should be in `.gitignore`
