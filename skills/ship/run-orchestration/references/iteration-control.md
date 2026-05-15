# Iteration Control & Guardrails

Each slice in the orchestration config has its own `iteration_budget`. Within a slice, execution operates in iteration cycles. Each iteration is one full dispatch-execute-review pass. This prevents runaway execution, gives the user control over cost/time per slice, and provides natural checkpoints.

## Per-Slice Iteration Budget

Unlike the original monolithic orchestration, iteration budgets are **per-slice**, not global. This means:

- Slice 1 with `iteration_budget: 6` gets up to 6 cycles
- Slice 2 with `iteration_budget: 10` gets up to 10 cycles
- Each slice's budget is independent — exhausting slice 1's budget doesn't affect slice 2
- If a slice completes early, remaining budget is unused (not transferred)

## Iteration Lifecycle

Each cycle within a slice follows this loop:

```
ITERATION START
  ├── Manager dispatches next batch (respecting burn rate + dependency graph)
  ├── Workers execute and report
  ├── Manager processes reports (unlock deps, handle failures, update task graph)
  ├── Tech Lead reviews completed work (if quality_gates.tech_lead_review is true)
  ├── QA Lead evaluates patterns + drift (every quality_gates.qa_lead_review_interval cycles)
  ├── Manager computes iteration summary
  └── Evaluate: continue, pause, or stop?
ITERATION END → increment counter → evaluate guardrails
```

## Iteration Summary

Produced every cycle. Flows up to Orchestrator for user reporting.

```yaml
iteration_summary:
  slice: "<slice name>"
  iteration: <current number>
  max_iterations: <iteration_budget>
  tasks_dispatched_this_cycle: <N>
  tasks_completed_this_cycle: <N>
  tasks_failed_this_cycle: <N>
  total_tasks_remaining: <N>
  total_tasks_completed: <N>
  total_tasks_in_slice: <N>
  completion_percentage: <0-100>
  burn_rate: "<tasks/iteration average>"
  velocity_trend: "accelerating | steady | decelerating | stalled"
  blockers:
    - task_id: "<T001>"
      reason: "<why stuck>"
  health: "green | yellow | red"
  recommendation: "continue | needs_user_input | escalate | stop"
```

**Health thresholds:**
- `green` — completion progressing, no recurring failures, on track
- `yellow` — minor issues (isolated failures, slight drift, velocity dip)
- `red` — systemic problems (failure cascade, stall, significant drift)

## Circuit Breakers

Automatic guardrails that prevent the system from spinning uselessly. When tripped, execution of the current slice pauses and Orchestrator escalates to user. Thresholds are configurable in `circuit_breakers` section of config.

### Stall Detection
- **Trigger:** `circuit_breakers.stall_threshold` consecutive iterations with 0 tasks completed (default: 3)
- **Action:** Pause slice and escalate — the system is stuck

### Failure Cascade
- **Trigger:** Failure rate exceeds `circuit_breakers.failure_cascade_threshold` (default: 50%) for `circuit_breakers.failure_cascade_window` consecutive iterations (default: 2)
- **Action:** Pause slice, mandatory Tech Lead review, escalate to user

### Drift Alarm
- **Trigger:** QA Lead reports `on_track: false` for `circuit_breakers.drift_alarm_window` consecutive iterations (default: 2)
- **Action:** Pause slice and escalate — building the wrong thing

### Infinite Loop Detection
- **Trigger:** Same task has failed and been re-queued more than `circuit_breakers.max_task_retries` times (default: 3)
- **Action:** Mark task as `dead`, notify Manager, continue if non-blocking; escalate if blocking

### Token Budget
- **Trigger:** Cumulative effort feels disproportionate to remaining work
- **Action:** Pause and report — let user decide whether to continue

## Circuit Breaker Recovery

When a circuit breaker trips, the user has these options:

1. **Resume** — fix the issue and continue: `run-orchestration --resume`
2. **Skip task** — mark the problematic task as dead and continue with remaining tasks
3. **Adjust config** — edit `.orchestration/config.yaml` (e.g., break a task into smaller pieces, change worker persona) and resume
4. **Ship partial** — accept current state, create PR with completed work: `run-orchestration --ship-slice`
5. **Abort slice** — skip this slice, proceed to next: `run-orchestration --skip-slice`
6. **Abort all** — stop everything

## Resumption Protocol

When execution stops (budget exhausted, breaker tripped, user-stopped), state is saved to `.orchestration/state.yaml`.

**State includes:**
- Which slices are completed, in-progress, or pending
- For in-progress slices: which tasks are completed, in-progress, queued, failed, or dead
- Branch names and PR URLs for completed slices
- Linear issue IDs created during execution

**To resume:** `run-orchestration --resume`
- Loads state.yaml and config.yaml
- Checks config hash — warns if config changed since last run
- Finds first non-completed slice
- Within that slice: restores task states, skips completed tasks
- Continues normal execution

**No work is repeated.** Completed tasks stay completed. Completed slices stay completed.

## Slice Completion Criteria

A slice is considered complete when:
1. All tasks in the slice are `completed` or `dead` (dead tasks are non-blocking), AND
2. Integration validation passes (build + test), AND
3. Final Tech Lead review is approved

If a slice's iteration budget is exhausted before completion:
1. Report what's done and what remains
2. Ask user: add more iterations, ship partial, or abort slice
3. Update state accordingly

## Mode Selection Guidance

Since budgets are per-slice, sizing guidance:

| Slice Complexity | Tasks | Recommended Budget |
|-----------------|-------|--------------------|
| Simple (2-3 tasks, one concern) | 2-3 | 4-6 |
| Medium (4-7 tasks, multiple components) | 4-7 | 8-12 |
| Complex (8-15 tasks, cross-cutting) | 8-15 | 12-18 |
| Very complex (break it down further) | 15+ | Split into multiple slices |
