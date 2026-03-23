---
name: code-review-gate
description: >-
  Tech Lead review gate for orchestration workflows. Reviews completed work
  for architectural quality, correctness, security, and codebase consistency.
  Returns a verdict (approved/needs_revision/rejected) with severity-tagged
  findings. Default skill for the Tech Lead role in run-orchestration.
  Use when dispatched as a code-reviewer subagent for quality gates.
version: 1.0.0
---

# Code Review Gate

Review completed work for architectural quality. Dispatched as a `code-reviewer` subagent by `run-orchestration` (Tech Lead role) or any orchestration skill that needs a quality gate.

## When Dispatched

- After each completed worker batch (if `quality_gates.tech_lead_review` is true)
- After N consecutive failures of a task
- Before slice/phase assembly (final review)
- When any orchestration skill needs an architectural checkpoint

## Input

The dispatching orchestrator provides:
- The mandate objective and acceptance criteria
- Completed task outputs and file changes
- Relevant codebase context (patterns, constraints)
- The diff to review (`git diff` or specific commit range)

## Review Criteria

1. **Correctness** — logic errors, edge cases, off-by-one, null handling
2. **Security** — hardcoded secrets, injection, unvalidated input, unsafe operations
3. **Maintainability** — readability, function size, naming, separation of concerns
4. **Architecture** — proper layering, no circular dependencies, follows existing patterns
5. **Testability** — adequate coverage, tests verify behavior not implementation
6. **Performance** — obvious inefficiencies, N+1 queries, unnecessary allocations

## Output Format

```yaml
review:
  task_id: "<TASK-ID or batch identifier>"
  verdict: "approved | needs_revision | rejected"
  concerns:
    - category: "correctness | security | performance | maintainability | testability | architecture"
      description: "<specific concern with file/line reference>"
      severity: "blocking | warning | suggestion"
      recommendation: "<what to do instead>"
  summary: "<1-2 sentence overall assessment>"
```

## Severity Definitions

| Severity | Meaning | Action |
|----------|---------|--------|
| **blocking** | Must fix before merge. Bugs, security holes, architectural violations | Orchestrator fixes immediately |
| **warning** | Should fix. Quality issues, missing error handling | Orchestrator fixes if straightforward |
| **suggestion** | Nice to have. Style improvements, optional enhancements | Noted for the user |

## Verdict Rules

- `approved` — zero blocking concerns
- `needs_revision` — blocking concerns exist but are fixable
- `rejected` — fundamental architectural problem requiring rethink

## Dispatch Template

```
You are the Tech Lead reviewing work for architectural quality.

MANDATE: {mandate objective}
ACCEPTANCE CRITERIA: {acceptance criteria list}
CONTEXT: {relevant codebase info, patterns, constraints}
DIFF/CHANGES: {git diff or file change summary}

Review criteria: correctness, security, maintainability, architecture, testability, performance.

Return a structured review with:
- verdict: approved | needs_revision | rejected
- For each concern: category, description, severity (blocking/warning/suggestion), recommendation
- summary: 1-2 sentence overall assessment
```

## Customization

To use a different review process, override in `.orchestration/config.yaml`:

```yaml
skills:
  tech_lead_review: "adlc:requesting-code-review"   # ADLC review process
```
