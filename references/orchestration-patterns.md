# Orchestration Patterns

Use the smallest orchestration pattern that gets the job done.

## Direct Persona

Use one persona when the question needs one perspective.

Examples:

- `code-reviewer` for a diff review.
- `security-specialist` for threat modeling.
- `debugger` for root cause analysis.

## Sequential Commands

Use sequential commands when work has a natural order:

```text
/refine -> /plan -> /execute -> /test -> /review -> /pr
```

Keep the user or main agent as the orchestrator so decisions stay visible.

## Parallel Fan-Out

Use fan-out only when each persona can inspect the same artifact independently.

Good examples:

- Code review, security review, and test coverage review of the same diff.
- Multiple implementation approaches explored in isolated worktrees.

Avoid router personas that only decide which other persona to call. They add
latency and paraphrasing without adding judgment.
