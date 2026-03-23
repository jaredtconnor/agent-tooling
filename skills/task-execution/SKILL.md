---
name: task-execution
description: >-
  Generic task execution for orchestration workers. Receives task context,
  implements the change, runs quality checks, and commits. Default skill for
  run-orchestration worker agents. Can be swapped for ADLC's executing-tasks
  (TDD), executing-chores (verification), or executing-bug-fixes (debug+TDD).
  Use when dispatched by run-orchestration for individual task execution.
version: 1.0.0
---

# Task Execution

Execute a single task fully: implement, verify, commit, report. Designed to be dispatched as an ephemeral worker subagent by `run-orchestration`.

## Input

The dispatching orchestrator provides a TASK CONTEXT block:

```
TASK: [task_id] [title]
ACCEPTANCE CRITERIA: [what done looks like]
CONTEXT: [relevant codebase info, architectural constraints, completed work outputs]
DEPENDENCIES COMPLETED: [list of prerequisite tasks and their outputs]
QUALITY COMMANDS: [build, test, lint commands from config]
```

## Execution Process

### Step 1: Understand

- Read the task context fully.
- If dependencies completed outputs are provided, review them for patterns and integration points.
- Identify the files to create or modify.

### Step 2: Implement

- Follow existing codebase conventions.
- Write tests alongside implementation (not strictly test-first — see Customization for TDD).
- Keep changes scoped to the task — do not fix unrelated issues.

### Step 3: Verify

Run the quality commands provided in the task context:

```bash
# Run whatever commands the config specifies
{test_command}     # e.g., just test, dotnet test, npm test
{lint_command}     # e.g., just lint (if configured)
{build_command}    # e.g., just build, dotnet build
```

All checks must pass before proceeding. If a check fails:
- Fix the issue and re-run (up to 3 attempts).
- If still failing after 3 attempts, report failure.

### Step 4: Report

Return a structured report:

```yaml
worker_report:
  task_id: "<T001>"
  status: "success | failure"
  output:
    deliverable: "<summary of what was built>"
    files_changed:
      - "path/to/file.ts (new | modified)"
    tests_added:
      - "path/to/test.ts — what it covers"
    notes: "<observations, caveats, patterns discovered>"
  failure_details:    # only if status == failure
    attempted: "<what was tried>"
    blocker: "<what prevented completion>"
    recommendation: "<what the orchestrator should know>"
```

## Rules

- **Complete the task fully or report failure.** No partial work without reporting.
- **Do not ask questions.** Use the context provided. If context is insufficient, report failure with details.
- **Do not work outside scope.** Only implement what the task describes.
- **Follow existing patterns.** Match the codebase's style, naming, and architecture.
- **3 attempts max.** If verification fails after 3 fix attempts, report failure.

## Customization

This is the **generic default**. For stricter workflows, swap in the YAML config:

| Config Value | Skill | Workflow |
|-------------|-------|----------|
| `"task-execution"` | This skill | Implement + verify (default) |
| `"adlc:executing-tasks"` | ADLC executing-tasks | Strict TDD (RED-GREEN-REFACTOR) |
| `"adlc:executing-chores"` | ADLC executing-chores | Verification-only (no TDD) |
| `"adlc:executing-bug-fixes"` | ADLC executing-bug-fixes | Systematic debugging + TDD |

Override in `.orchestration/config.yaml`:

```yaml
skills:
  task_execution: "adlc:executing-tasks"   # Use ADLC TDD workflow
```
