---
name: todoist-inbox-triage
description: >-
  Triage a Todoist inbox into GTD-style projects, priorities, labels, and due
  dates using the `td` CLI. Use when the user asks to organize, clean up,
  process, or triage their Todoist inbox, or wants overdue/undated tasks
  sorted into projects with sensible priorities and labels.
version: 1.0.0
---

# Todoist Inbox Triage

Process every item sitting in a Todoist Inbox into the right project, with a
real priority, label, and due date — following GTD-style processing rules.
Requires the `td` CLI (`@doist/todoist-cli`), already authenticated
(`td auth status`).

## When to use this

- User says "organize/clean up/triage my Todoist [inbox]"
- Inbox has accumulated unprocessed items, especially overdue ones
- User wants a batch reorganization rather than one-off task edits

## Workflow

### 1. Inventory the inbox

```bash
td inbox --json --all
```

Note each task's `id`, `content`, and current `due` string. Also pull the
project list so you know valid `--project` targets:

```bash
td project list
```

### 2. Classify each task (GTD triage questions)

For every inbox item, ask in order:

1. **Does this still need doing?** If the window has passed (e.g. a
   "Plan Q3" task found in September) or it's clearly stale/duplicate,
   delete it — don't silently reschedule dead tasks forward.
2. **Is it actionable now?** If not, move to a Someday-Maybe project instead
   of leaving it in Inbox or forcing a fake due date.
3. **What's the right project?**
   - One-off task tied to an ongoing responsibility → an Area project
     (Home & Household, Finances, Health, Learning & Growth, etc.)
   - Part of a multi-step deliverable → an Active Project
   - Recurring cadence → a Routines sub-project (Daily/Weekly/Monthly)
   - Reference/non-actionable → a Lists project

Then assign: **Project** + **Priority** + **Label** + **Due date** (if
time-bound). Group obviously related tasks (e.g. multiple car-repair items)
as subtasks under one parent instead of leaving them as flat siblings.

**Priority guide:**
| Priority | Meaning |
|---|---|
| p1 | Must do very soon / time-critical (e.g. renewals, deadlines) |
| p2 | Should do this week/month — real commitment |
| p3 | Do when time allows |
| p4 | Someday/low priority — usually paired with `--no-due` |

**Label guide (context tags, adjust to the user's actual label set via `td label list`):**
`errand`, `focus`, `easy`, `call`, `waiting`, `home`, `evening` — pick ones
that describe HOW/WHERE the task gets done, not what it's about.

### 3. Apply changes with `td`

`td task update` does **not** accept `--project` — move first, then update:

```bash
# Move to project (by name or id:xxx)
td task move id:<taskid> --project "Home & Household"

# Then set priority / due / labels
td task update id:<taskid> --priority p2 --due "next week" --labels "errand"

# Remove a due date entirely (for Someday-Maybe / p4 items)
td task update id:<taskid> --priority p4 --no-due

# Nest related tasks under a parent
td task move id:<childid> --parent id:<parentid>

# Delete stale/dead tasks (requires --yes to actually delete)
td task delete id:<taskid> --yes
```

Batch these as shell one-liners chained per task; run project moves for all
tasks first, then priority/due/label updates, then parent-nesting, then
deletes — this order avoids re-fetching IDs between steps.

### 4. Verify

```bash
td inbox
```

Should print "No tasks found." when triage is complete. If items remain,
they were skipped — check why before reporting done.

## Notes / pitfalls

- `td task list --json` prints `"priority": 3` for P2 — Todoist's API stores
  priority inverted (4=P1, 3=P2, 2=P3, 1=P4). Use `td task view <id>` for the
  human-readable `Priority: pN` form when double-checking.
- `td task delete` without `--yes` only previews ("Would delete: ..."). You
  must re-run with `--yes` to actually delete — treat this as an implicit
  confirmation step, not a bug.
- If `td` commands hang/fail with `AUTH_STORE_READ_FAILED` in one runtime but
  work in a plain terminal, the credential is in a keyring not shared with
  that sandbox — run `td` commands via the terminal tool directly, not through
  a code-execution sandbox.
- Get explicit user sign-off on the triage *plan* (or at least the project/
  priority scheme) before applying bulk moves/deletes to an inbox with many
  items — this is a destructive-adjacent bulk operation.
