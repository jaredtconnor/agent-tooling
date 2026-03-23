---
name: dev-review
description: >-
  Lightweight code review for the dev workflow. Reviews git diff of unstaged
  changes, categorizes findings by severity (Critical/High/Medium), and returns
  a structured report. Use when dispatched by the dev skill for Phase 4 review,
  or when the user wants a quick code review of recent changes.
version: 1.0.0
---

# Dev Review

Review all changes in the working tree and produce a severity-categorized report. Designed to be dispatched as a `code-reviewer` subagent by the `dev` skill (Phase 4), but also usable standalone.

## Input

The dispatching skill provides:
- A `git diff` of all changes (staged + unstaged)
- The original requirement or objective
- A summary of what was implemented

## Review Process

1. **Read the full diff** — understand every change before judging any of them.
2. **Check correctness** — logic errors, off-by-one, null/undefined handling, missing edge cases.
3. **Check security** — hardcoded secrets, injection vectors, unsafe deserialization, unvalidated input.
4. **Check maintainability** — naming clarity, function size, separation of concerns, duplication.
5. **Check consistency** — does the new code follow existing patterns in the codebase?
6. **Check test coverage** — are the changes tested? Are edge cases covered?

## Output Format

Return a structured report:

```yaml
review:
  verdict: "approved | needs_revision"
  findings:
    - severity: "critical"    # Must fix before proceeding
      category: "correctness | security | performance | maintainability | testability"
      file: "path/to/file.ts"
      description: "What's wrong"
      recommendation: "How to fix it"
    - severity: "high"        # Should fix before proceeding
      category: "..."
      file: "..."
      description: "..."
      recommendation: "..."
    - severity: "medium"      # Fix if straightforward, otherwise note for user
      category: "..."
      file: "..."
      description: "..."
      recommendation: "..."
  summary: "1-2 sentence overall assessment"
```

## Severity Definitions

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| **Critical** | Bug, security hole, data loss risk | Must fix immediately |
| **High** | Significant quality issue, missing error handling | Fix before proceeding |
| **Medium** | Style, minor improvement, optional enhancement | Fix if easy, otherwise note |

## Rules

- Be specific — cite file paths and line numbers, not vague concerns.
- Be pragmatic — don't flag style preferences as Critical.
- One finding per issue — don't bundle unrelated concerns.
- If the diff is clean, say so. Don't invent findings to seem thorough.
- Verdict is `approved` only when zero Critical and zero High findings remain.

## Dispatch Template

When the `dev` skill dispatches this review, it should use:

```
You are reviewing code changes for quality, correctness, and security.

OBJECTIVE: {what was being built}
IMPLEMENTATION SUMMARY: {what was actually built}
DIFF: {git diff output}

Review using the dev-review skill's process and output format.
Return your findings as a structured YAML report.
```

## Customization

To use a different review process (e.g., ADLC's `requesting-code-review`), edit the `dev` skill's Phase 4 to reference a different review skill. This skill can be swapped without changing the dev workflow.
