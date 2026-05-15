# Setup Examples

## Example 1: Linear Ticket → YAML Config

**Input:**
```
orchestration-setup CAL-123
```

**What happens:**
1. Fetches `CAL-123` via `linctl issue get CAL-123 --json`
2. Extracts title: "Add batch cancellation support to CalcEngine"
3. Extracts description, labels, project info
4. Explores codebase: discovers .NET Clean Architecture, existing batch domain model, health endpoint pattern
5. Decomposes into 3 slices based on dependency ordering
6. Writes `.orchestration/config.yaml`

**Generated config (abbreviated):**

```yaml
version: "1.0"

source:
  type: "linear"
  ref: "CAL-123"
  raw_title: "Add batch cancellation support to CalcEngine"

mandate:
  objective: "Add batch cancellation support allowing users to cancel running batches via API"
  constraints:
    - "Workers must finish current job before honoring cancellation"
    - "Cancellation must be idempotent"
    - "Must work with existing container health protocol"
  acceptance_criteria:
    - "PATCH /v1/api/batches/{id}/cancel returns 200"
    - "Workers detect cancellation via health endpoint within 30s"
    - "BatchCancelled event published to Service Bus"
    - "All existing tests pass"
  context:
    - "Batch states: Submitted, Running, Completed, Failed"
    - "Workers poll health endpoint every 30s"
    - "Clean Architecture: Domain → Application → Infrastructure → API"

platform:
  git_remote: "github"
  cli_tool: "gh"
  default_branch: "main"
  linear:
    team: "OLDALM"
    project: "CalcEngine"
    parent_issue: "CAL-123"

slices:
  - name: "Foundation — batch state infrastructure"
    branch_suffix: "batch-state-infrastructure"
    iteration_budget: 6
    issues:
      - title: "Batch State Enum and Transitions"
        description: "Add Cancelling and Cancelled states to BatchStatus"
        labels: ["backend", "domain"]
        acceptance_criteria:
          - "New states exist in enum"
          - "State machine validates transitions"
        tasks:
          - id: "T001"
            title: "Add Cancelling/Cancelled to BatchStatus enum"
            worker_persona: "backend_engineer"
            depends_on: []
            size: "small"
            acceptance_criteria: "Enum includes new states, existing code compiles"
          - id: "T002"
            title: "Implement state transition validation"
            worker_persona: "backend_engineer"
            depends_on: ["T001"]
            size: "small"
            acceptance_criteria: "Invalid transitions throw, valid transitions succeed"
          - id: "T003"
            title: "Unit tests for state transitions"
            worker_persona: "qa_engineer"
            depends_on: ["T002"]
            size: "small"
            acceptance_criteria: "All valid/invalid transitions tested"

  - name: "Cancel endpoint and events"
    branch_suffix: "cancel-endpoint"
    iteration_budget: 10
    issues:
      - title: "Cancel API Endpoint"
        description: "PATCH /v1/api/batches/{id}/cancel"
        labels: ["backend", "api"]
        tasks:
          - id: "T001"
            title: "Add cancel endpoint to BatchController"
            worker_persona: "backend_engineer"
            depends_on: []
            size: "medium"
            acceptance_criteria: "Endpoint exists, returns 200 on valid cancel, 409 on invalid state"
          - id: "T002"
            title: "Implement cancellation domain service"
            worker_persona: "backend_engineer"
            depends_on: ["T001"]
            size: "medium"
            acceptance_criteria: "Service transitions batch, publishes domain event"
      - title: "Health Endpoint Cancellation Flag"
        description: "Add ShouldCancel to health response"
        labels: ["backend"]
        tasks:
          - id: "T003"
            title: "Add ShouldCancel flag to health response DTO"
            worker_persona: "backend_engineer"
            depends_on: []
            size: "small"
            acceptance_criteria: "Health endpoint returns ShouldCancel: true for cancelling batches"
      - title: "Service Bus Cancellation Event"
        description: "Publish BatchCancelled event"
        labels: ["backend", "integration"]
        tasks:
          - id: "T004"
            title: "Publish BatchCancelled event to Service Bus"
            worker_persona: "backend_engineer"
            depends_on: ["T002"]
            size: "small"
            acceptance_criteria: "Event published on cancellation, includes batch metadata"

  - name: "Integration tests"
    branch_suffix: "cancel-integration-tests"
    iteration_budget: 6
    issues:
      - title: "Cancellation Integration Tests"
        labels: ["testing"]
        tasks:
          - id: "T001"
            title: "Integration test: full cancellation flow"
            worker_persona: "qa_engineer"
            depends_on: []
            size: "medium"
            acceptance_criteria: "Test covers: cancel request → state transition → health flag → event published"

quality_gates:
  tech_lead_review: true
  qa_lead_review_interval: 3
  build_command: "dotnet build"
  test_command: "dotnet test"
  lint_command: null

circuit_breakers:
  stall_threshold: 3
  failure_cascade_threshold: 0.5
  failure_cascade_window: 2
  max_task_retries: 3
  drift_alarm_window: 2

workers:
  max_concurrent: 4
  persona_mapping:
    backend_engineer: "backend-engineer"
    frontend_engineer: "frontend-engineer"
    qa_engineer: "qa-engineer"
```

**Summary output:**
```
## Orchestration Plan Summary

**Source:** CAL-123 — Add batch cancellation support to CalcEngine
**Slices:** 3 | **Issues:** 5 | **Tasks:** 8

### Slice 1: Foundation — batch state infrastructure
Branch: feature/CAL-123-batch-state-infrastructure
Issues: 1 | Tasks: 3 | Budget: 6 iterations

  Issue 1.1: Batch State Enum and Transitions (3 tasks)
    T001 [backend_engineer/small] Add Cancelling/Cancelled to BatchStatus enum
    T002 [backend_engineer/small] Implement state transition validation
    T003 [qa_engineer/small] Unit tests for state transitions

### Slice 2: Cancel endpoint and events
Branch: feature/CAL-123-cancel-endpoint
Issues: 3 | Tasks: 4 | Budget: 10 iterations

  Issue 2.1: Cancel API Endpoint (2 tasks)
    T001 [backend_engineer/medium] Add cancel endpoint to BatchController
    T002 [backend_engineer/medium] Implement cancellation domain service
  Issue 2.2: Health Endpoint Cancellation Flag (1 task)
    T003 [backend_engineer/small] Add ShouldCancel flag to health response DTO
  Issue 2.3: Service Bus Cancellation Event (1 task)
    T004 [backend_engineer/small] Publish BatchCancelled event to Service Bus

### Slice 3: Integration tests
Branch: feature/CAL-123-cancel-integration-tests
Issues: 1 | Tasks: 1 | Budget: 6 iterations

  Issue 3.1: Cancellation Integration Tests (1 task)
    T001 [qa_engineer/medium] Integration test: full cancellation flow

---
Config written to: .orchestration/config.yaml
Review and edit the YAML, then run /run-orchestration to execute.
```

## Example 2: Markdown Plan File

**Input:**
```
orchestration-setup ./plans/testing-pyramid.md
```

**What happens:**
1. Reads `./plans/testing-pyramid.md`, extracts YAML frontmatter or parses markdown structure
2. Explores codebase to understand existing test infrastructure
3. Decomposes into slices by test level (L1 unit → L2 integration → L3 e2e)
4. Writes `.orchestration/config.yaml`
5. Prints summary table

## Example 3: Inline Description

**Input:**
```
orchestration-setup "Add rate limiting middleware to all API endpoints"
```

**What happens:**
1. Parses as inline description
2. May ask clarifying questions: "What rate limits? Per-user or global? Which endpoints?"
3. Explores codebase to find API layer, middleware patterns, existing auth middleware as template
4. Decomposes into 2 slices: middleware infrastructure, then per-endpoint integration
5. Sets `platform.linear` to `null` (no ticket to link)
6. Writes config and prints summary

## Example 4: Notion Page

**Input:**
```
orchestration-setup https://notion.so/workspace/API-Migration-Plan-abc123
```

**What happens:**
1. Detects Notion URL, fetches via `notion-fetch`
2. Extracts structured content from page headings and body
3. Explores codebase for migration targets
4. Decomposes into slices based on migration phases
5. Sets `platform.linear` to `null` unless user specifies
6. Writes config and prints summary
