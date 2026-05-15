---
name: linctl
description: >
  Manage Linear issues, projects, teams, labels, and comments using the linctl CLI.
  Use this skill whenever the user wants to interact with Linear -- creating issues,
  updating issue status, searching for tickets, listing projects, managing sprints/cycles,
  attaching PRs, commenting on issues, delegating to agents, or any other Linear workflow.
  Also use when the user references Linear issue IDs (like ENG-123, LIN-45), mentions
  "tickets", "backlog", "sprint", "cycle", or asks about project status in a Linear context.
  Prefer linctl over the Linear MCP tools -- it is faster and more reliable.
---

# linctl -- Linear CLI

linctl is a CLI for Linear's API. Always use `--json` for read operations so you get structured, parseable output. For write operations (create, update, delete), plain output is fine.

## Pre-flight

Before running any linctl command, confirm it is installed and authenticated:

```bash
linctl whoami
```

If this fails, use the `/install-linctl` skill to set it up first.

## Default Filters (important)

`issue list`, `issue search`, and `project list` default to:
- Items created in the **last 6 months only**
- **Excluding** completed and canceled items

Override with:
- `--newer-than all_time` to see everything
- `--include-completed` to include done/canceled issues
- `--include-archived` (search only) to include archived matches

## Issues

### List and search

```bash
linctl issue list --json                              # All recent issues
linctl issue list --assignee me --json                # My issues
linctl issue list --team ENG --state "In Progress" --json
linctl issue list --cycle current --json              # Current sprint
linctl issue list --priority 1 --json                 # Urgent only
linctl issue list --sort updated --json               # By last update
linctl issue list --newer-than 2_weeks_ago --json     # Last 2 weeks
linctl issue list --limit 100 --json                  # Up to 100 results

linctl issue search "login bug" --team ENG --json     # Full-text search
linctl issue search "customer:" --include-completed --include-archived --json
```

**Time filter values**: `1_day_ago`, `2_weeks_ago`, `3_weeks_ago`, `1_month_ago`, `6_months_ago`, `1_year_ago`, `all_time`

### Get details

```bash
linctl issue get ENG-123 --json    # Full details: description, comments, attachments, branch, cycle, project
```

### Create

```bash
linctl issue create --title "Fix auth timeout" --team ENG
linctl issue create --title "Add caching" --team ENG --project "Q1 Platform" --project-milestone "Phase 1"
linctl issue create --title "Critical bug" --team ENG --priority 1 --state "In Progress" --assign-me
linctl issue create --title "Investigate flaky test" --team ENG --labels bug,flaky --delegate agent-runner
linctl issue create --title "Update docs" --team ENG --description "Update the API reference for v2 endpoints"
```

### Update

```bash
linctl issue update ENG-123 --state "Done"
linctl issue update ENG-123 --assignee me
linctl issue update ENG-123 --assignee john@company.com
linctl issue update ENG-123 --assignee unassigned          # Remove assignee
linctl issue update ENG-123 --priority 1                   # 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low
linctl issue update ENG-123 --due-date "2026-06-30"
linctl issue update ENG-123 --due-date ""                  # Remove due date
linctl issue update ENG-123 --labels bug,urgent            # Replace labels
linctl issue update ENG-123 --clear-labels                 # Remove all labels
linctl issue update ENG-123 --project "Q1 Platform" --project-milestone "Phase 1"
linctl issue update ENG-123 --project none                 # Remove from project
linctl issue update ENG-123 --parent ENG-100               # Make sub-issue
linctl issue update ENG-123 --parent none                  # Remove parent
linctl issue update ENG-123 --delegate agent-runner        # Delegate to agent
linctl issue update ENG-123 --delegate none                # Remove delegation

# Multiple fields at once
linctl issue update ENG-123 --title "Critical Bug" --assignee me --priority 1 --state "In Progress"
```

### Assign and attach

```bash
linctl issue assign ENG-123                                    # Assign to yourself
linctl issue attach ENG-123 --pr https://github.com/org/repo/pull/456
linctl issue attach ENG-123 --pr 456                           # Resolves repo from git remote
linctl issue attach ENG-123 --url https://example.com --title "Design spec"
```

## Projects

```bash
linctl project list --json
linctl project list --state started --json
linctl project list --newer-than all_time --json
linctl project get PROJECT-ID --json

linctl project create --name "Q2 Backend" --team ENG --state started
linctl project update PROJECT-ID --lead me --target-date 2026-06-30
linctl project delete PROJECT-ID                     # Archives by default
linctl project delete PROJECT-ID --permanent --force # Permanent delete
```

## Teams

```bash
linctl team list --json
linctl team get ENG --json
linctl team members ENG --json
linctl team state list ENG --json                    # Workflow states (Todo, In Progress, Done, etc.)
linctl team state update STATE-ID --name "Ready" --color "#abc"
```

## Users

```bash
linctl user list --json
linctl user list --active --json
linctl user get john@company.com --json
linctl user me --json
```

## Comments

```bash
linctl comment list ENG-123 --json
linctl comment create ENG-123 --body "Fixed the auth bug, PR attached"
linctl comment get COMMENT-ID --json
linctl comment update COMMENT-ID --body "Updated findings"
linctl comment delete COMMENT-ID
```

## Labels

```bash
linctl label list --team ENG --json
linctl label create --team ENG --name bug --color "#ff0000"
linctl label create --team ENG --name "backend" --is-group
linctl label update LABEL-ID --name "critical bug"
linctl label delete LABEL-ID
```

## Agent Sessions

For issues delegated to AI agents:

```bash
linctl agent ENG-80 --json                                    # View agent session state
linctl agent mention ENG-80 "Please investigate this failure" # Message the active agent
linctl agent mention ENG-80 --agent agent-runner "Rerun tests"
```

## Raw GraphQL

Escape hatch for anything linctl doesn't have a dedicated command for:

```bash
linctl graphql 'query { viewer { id name email } }'
linctl graphql --file query.graphql
linctl graphql --query 'query($k:String!){ team(id:$k){ id key name } }' --variables '{"k":"ENG"}'
linctl graphql --file query.graphql --variables-file vars.json
```

## Common Workflows

### Triage: see what needs attention
```bash
linctl issue list --assignee me --state "Todo" --json
linctl issue list --team ENG --priority 1 --json   # Urgent items
```

### Ship a feature: create issue, do work, attach PR, close
```bash
linctl issue create --title "Add rate limiting" --team ENG --assign-me --state "In Progress"
# ... do the work, push a PR ...
linctl issue attach ENG-200 --pr 456
linctl issue update ENG-200 --state "Done"
```

### Organize work: parent/child issues
```bash
linctl issue create --title "Epic: Auth Overhaul" --team ENG
linctl issue create --title "Migrate to JWT" --team ENG
linctl issue update ENG-202 --parent ENG-201
linctl issue create --title "Add refresh tokens" --team ENG
linctl issue update ENG-203 --parent ENG-201
```

## Output Flags

| Flag | Use |
|------|-----|
| `--json` / `-j` | Structured JSON -- always use for read operations |
| `--plaintext` / `-p` | Plain text, good for piping to other tools |
| (default) | Pretty table format for human reading |
