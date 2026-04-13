# Tiered Test Gate Framework

Comprehensive reference for the QA readiness review skill. Defines each tier, scoring criteria, agentic readiness requirements, and the full report template.

---

## Tier Definitions

### Tier 0: Local / Pre-commit

**Purpose:** Catch obvious issues before code leaves the developer's machine. For agents, this is the primary self-verification loop.

**Target duration:** <30 seconds

**What belongs here:**
- Linting (syntax, style, formatting)
- Type checking (static type analysis)
- Unit tests (fast, isolated, no I/O)
- Pre-commit hooks (automated on `git commit`)
- Code formatting (auto-fix)

**Detection patterns:**
- `.pre-commit-config.yaml` with hooks defined
- `.husky/*` or `lefthook.yml` with pre-commit hooks
- Linter configs: `.eslintrc*`, `ruff.toml`, `pyproject.toml [tool.ruff]`, `.golangci.yml`, `clippy.toml`
- Type checker configs: `tsconfig.json` (check `strict`), `mypy.ini`, `pyrightconfig.json`
- Formatter configs: `.prettierrc*`, `biome.json`, `rustfmt.toml`
- Fast test commands in justfile/Makefile/package.json

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No local quality checks detected |
| 1-2 | Formatter OR linter exists but no pre-commit automation |
| 3-4 | Linter + formatter exist, partial pre-commit hooks |
| 5-6 | Linter + formatter + type checking, pre-commit hooks present |
| 7-8 | Full pre-commit suite (lint, format, type check, fast unit tests), <30s |
| 9-10 | All of above + optimized for speed, incremental checks, excellent dev UX |

**Agentic readiness:** Can agents run lint + type check + unit tests locally in under 30 seconds? If yes, agents can self-verify every change before committing.

---

### Tier 1: Branch / PR

**Purpose:** Automated checks on every push to a branch or PR. First CI gate before human review.

**Target duration:** <5 minutes

**What belongs here:**
- Full unit test suite
- Integration tests (fast, mocked external deps)
- Lint checks (full project, not just changed files)
- Type checking (full project)
- Build verification (does it compile/build?)
- Code coverage reporting

**Detection patterns:**
- CI workflow files triggered on `push` or `pull_request`
- Test jobs in CI that run on every PR
- Coverage reporting steps (Codecov, Coveralls, built-in)
- Required status checks (branch protection)

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No CI pipeline detected |
| 1-2 | CI exists but does not run tests |
| 3-4 | CI runs some tests, not comprehensive |
| 5-6 | CI runs full test suite + lint, but slow (>5min) or not required |
| 7-8 | Full test suite + lint + type check + build, <5min, required for merge |
| 9-10 | All of above + parallel jobs, caching, coverage gates, fast feedback |

**Agentic readiness:** Does CI block PRs on test failure? If CI is advisory-only, agents cannot rely on it to catch regressions.

---

### Tier 2: Merge to Main

**Purpose:** Comprehensive gate before code reaches the main branch. Everything that Tier 1 runs, plus broader integration checks.

**Target duration:** <15 minutes

**What belongs here:**
- Everything from Tier 1
- Integration tests with real dependencies (databases, queues)
- Contract tests (API compatibility)
- Migration verification
- Multi-platform/matrix builds
- Documentation generation checks

**Detection patterns:**
- CI jobs triggered on merge to `main`/`master`/`develop`
- Separate merge workflow or additional jobs in PR workflow
- Contract test configs (`pact*`, `openapi*`)
- Database migration test steps
- Matrix build configs (multiple OS/language versions)

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No merge-specific gates (same as branch CI or nothing) |
| 1-2 | Branch CI runs on merge but no additional checks |
| 3-4 | Some integration tests run on merge |
| 5-6 | Integration tests + contract tests, merge is gated |
| 7-8 | Comprehensive merge gate: integration, contract, migration, matrix |
| 9-10 | All of above + canary/staged rollout triggers, deployment verification |

**Agentic readiness:** Are merge gates comprehensive enough that agents can trust merged code is production-viable?

---

### Tier 3: On-Demand E2E / Acceptance

**Purpose:** End-to-end and acceptance tests that verify full user journeys. Run on demand or on release branches.

**Target duration:** <30 minutes

**What belongs here:**
- E2E tests (Playwright, Cypress, Selenium)
- Acceptance tests (BDD/Gherkin, behavior specs)
- Smoke tests for deployments
- Visual regression tests
- API integration tests against staging

**Detection patterns:**
- E2E framework configs: `playwright.config*`, `cypress.config*`, `wdio.conf*`
- BDD files: `*.feature`, cucumber configs, behave configs
- E2E test directories: `e2e/`, `tests/e2e/`, `integration/`, `acceptance/`
- GIVEN/WHEN/THEN patterns in test files
- Smoke test scripts or CI jobs

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No E2E or acceptance tests detected |
| 1-2 | E2E framework installed but few/no test files |
| 3-4 | Some E2E tests exist, no acceptance/BDD tests |
| 5-6 | E2E tests cover main user journeys, some acceptance tests |
| 7-8 | Comprehensive E2E + acceptance tests, runnable on demand |
| 9-10 | All of above + visual regression, structured BDD, clear acceptance criteria |

**Agentic readiness:** Do E2E/acceptance tests exist and can they be run programmatically? Agents need to verify end-to-end behavior after significant changes.

---

### Tier 4: Performance

**Purpose:** Detect performance regressions before they reach production. Run on-demand or as part of release process.

**Target duration:** Variable (minutes to hours)

**What belongs here:**
- Load tests (k6, Locust, JMeter, Artillery)
- Benchmark suites (language-native benchmarks)
- Stress tests
- Memory leak detection
- Database query performance tests

**Detection patterns:**
- Performance tool configs: `k6*`, `locustfile*`, `*.jmx`, `artillery*`
- Benchmark directories: `bench/`, `benchmarks/`, `perf/`
- Language-specific benchmarks: `*_bench_test.go`, `bench_*.py`, `*.bench.ts`
- Performance CI jobs (scheduled or on-demand)
- Mutation testing configs: `stryker*`, `mutmut*`, `pitest*`

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No performance testing detected |
| 1-2 | Benchmark files exist but no automation |
| 3-4 | Basic load test or benchmark suite, manual execution |
| 5-6 | Automated performance tests, some CI integration |
| 7-8 | Comprehensive performance suite, regression detection, CI integrated |
| 9-10 | All of above + baseline tracking, alerting, mutation testing |

**Agentic readiness:** Are performance tests available on-demand so agents can verify performance-sensitive changes?

---

### Tier 5: Security / Compliance

**Purpose:** Security scanning and compliance verification. Run on schedule or triggered by dependency changes.

**Target duration:** Variable

**What belongs here:**
- SAST (static application security testing)
- DAST (dynamic application security testing)
- Dependency vulnerability scanning (Dependabot, Snyk, Trivy)
- License compliance scanning
- Secret detection
- Container image scanning

**Detection patterns:**
- Security tool configs: `.snyk`, `.trivyignore`, `semgrep*`
- Dependency management: `dependabot.yml`, `renovate.json`, `.github/dependabot.yml`
- Secret detection: `.gitleaks.toml`, `.secretlintrc*`, `detect-secrets`
- Security CI jobs (SAST/DAST steps in pipeline)
- Container scanning configs

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No security scanning detected |
| 1-2 | Dependabot/Renovate for dependency updates only |
| 3-4 | Dependency scanning + basic SAST |
| 5-6 | SAST + dependency scanning + secret detection |
| 7-8 | Comprehensive scanning: SAST, dependency, secrets, license compliance |
| 9-10 | All of above + DAST, container scanning, compliance gates, automated remediation |

**Agentic readiness:** Are security/compliance scans configured so agents do not introduce vulnerabilities?

---

## Pipeline Stage Assessment

Assess the repository through five pipeline stages. Each stage maps to activities in the development workflow.

### Write

**What to assess:**
- Are there code generation templates or scaffolding tools?
- Do test templates exist (test generators, snapshot tooling)?
- Is there a consistent project structure that guides where new code goes?
- Are there coding standards documented (CLAUDE.md, CONTRIBUTING.md)?

### Check

**What to assess:**
- What linting rules are enforced? How strict?
- Is type checking enabled? What strictness level?
- Is formatting automated (format-on-save, pre-commit)?
- Are static analysis tools configured (SonarQube, CodeClimate, Semgrep)?
- How fast do checks run locally?

### Test

**What to assess:**
- What test frameworks are in use?
- What types of tests exist (unit, integration, e2e, contract, acceptance)?
- What is the approximate test-to-code ratio?
- Are tests categorized and independently runnable?
- How fast is the full test suite?

### Review

**What to assess:**
- Is code review enforced (branch protection, required reviewers)?
- Are there CODEOWNERS files?
- Do PR templates exist?
- Is there automated review tooling (Danger.js, review bots)?
- Are review checklists defined?

### Deploy

**What to assess:**
- Is there a CI/CD pipeline for deployment?
- Are there staging/preview environments?
- Is deployment gated on test results?
- Are rollback mechanisms in place?
- Is there deployment monitoring/alerting?

---

## Agentic Readiness Criteria

Summary of what makes a repository "agent-ready" at each tier:

| Tier | Agent-Ready When |
|------|-----------------|
| 0 | Agents can run lint + type check + unit tests locally in <30s with a single command |
| 1 | CI blocks PRs on test failure; agents get pass/fail signal within 5min |
| 2 | Merge gates are comprehensive; agents can trust merged code is production-viable |
| 3 | E2E/acceptance tests exist and are runnable programmatically on demand |
| 4 | Performance tests are available so agents can verify performance-sensitive changes |
| 5 | Security scans are configured so agents do not introduce vulnerabilities |

**Minimum for agentic development:** Tier 0 score >= 7 and Tier 1 score >= 7.

Without fast local feedback (Tier 0) and reliable CI (Tier 1), agents cannot self-verify and require constant human oversight.

---

## Report Template

```markdown
# QA Readiness Review - [Repository Name]

**Date:** YYYY-MM-DD
**Reviewed by:** Claude Code (QA Review Skill v1.0.0)
**Repository:** [path or URL]

## Executive Summary

| Metric | Value |
|--------|-------|
| Overall QA Readiness | X/10 |
| Agentic Engineering Ready | Ready / Partial / Not Ready |
| Primary Constraint | [identified bottleneck] |
| Languages Detected | [list] |
| Test Framework(s) | [list] |

## Tier Assessment

| Tier | Stage | Target | Score | Status |
|------|-------|--------|-------|--------|
| 0 | Local / Pre-commit | <30s | X/10 | [emoji + word] |
| 1 | Branch / PR | <5min | X/10 | [emoji + word] |
| 2 | Merge to main | <15min | X/10 | [emoji + word] |
| 3 | On-demand E2E | <30min | X/10 | [emoji + word] |
| 4 | Performance | Variable | X/10 | [emoji + word] |
| 5 | Security / Compliance | Variable | X/10 | [emoji + word] |

Status indicators: Strong (>=7), Moderate (4-6), Weak (1-3), Absent (0)

## Pipeline Stage Analysis

### Write
[findings about how code and tests are authored, scaffolding, templates, standards]

### Check
[findings about linting, type checks, static analysis, formatting]

### Test
[findings about unit, integration, E2E, contract, acceptance tests]

### Review
[findings about code review process, branch protection, PR templates]

### Deploy
[findings about CI/CD pipeline, staging, deployment gates]

## Testing Infrastructure Detected

### Test Frameworks
| Framework | Config File | Test Files | Type |
|-----------|-------------|------------|------|
| [name] | [path] | [count] | [unit/integration/e2e] |

### Quality Tools
| Tool | Config File | Purpose |
|------|-------------|---------|
| [name] | [path] | [lint/format/type-check/static-analysis] |

### CI/CD Platform
| Platform | Config File | Triggers |
|----------|-------------|----------|
| [name] | [path] | [push/PR/merge/schedule] |

### Testing Abstractions
| Runner | File | Commands Available |
|--------|------|--------------------|
| [just/make/npm] | [path] | [test, lint, format, build, ...] |

## Tier-by-Tier Detail

### Tier 0: Local / Pre-commit (X/10)

**Detected:**
- [list of pre-commit hooks, linters, formatters, type checkers]

**Missing / Gaps:**
- [what is absent or incomplete]

**Estimated local check duration:** [if determinable]

### Tier 1: Branch / PR (X/10)

**Detected:**
- [CI jobs that run on PR, what they check]

**Missing / Gaps:**
- [what is absent or incomplete]

**PR blocking:** [Yes - required status checks / No - advisory only / Unknown]

### Tier 2: Merge to Main (X/10)

**Detected:**
- [additional merge-time checks beyond Tier 1]

**Missing / Gaps:**
- [what is absent or incomplete]

### Tier 3: On-Demand E2E (X/10)

**Detected:**
- [E2E frameworks, acceptance tests, feature files]

**Missing / Gaps:**
- [what is absent or incomplete]

### Tier 4: Performance (X/10)

**Detected:**
- [load test tools, benchmarks, performance CI jobs]

**Missing / Gaps:**
- [what is absent or incomplete]

### Tier 5: Security / Compliance (X/10)

**Detected:**
- [security scanners, dependency management, secret detection]

**Missing / Gaps:**
- [what is absent or incomplete]

## Foundations Recommendations

For each gap, a specific remediation action is provided. Gaps that map to foundations skills include the exact skill or command to run.

### Quick Start

[If 2+ critical gaps map to foundations skills, recommend:]

```
/setup
```

This orchestrates: PM configuration, CLAUDE.md generation, justfile creation, pre-commit setup.

### Critical (Address First — Tier 0/1 gaps blocking agent self-verification)

| # | Gap | Current State | Target State | Action | Tier Impact |
|---|-----|--------------|-------------|--------|-------------|
| 1 | [gap title] | [what exists] | [best practice] | `Skill(<skill>)` or manual step | Tier X: +N |

### Important (Near-term — reduce agent friction)

| # | Gap | Current State | Target State | Action | Tier Impact |
|---|-----|--------------|-------------|--------|-------------|
| 1 | [gap title] | [what exists] | [best practice] | `Skill(<skill>)` or manual step | Tier X: +N |

### Nice-to-Have (Long-term — higher-tier maturity)

| # | Gap | Current State | Target State | Action | Tier Impact |
|---|-----|--------------|-------------|--------|-------------|
| 1 | [gap title] | [what exists] | [best practice] | Manual step | Tier X: +N |

### Common Gap-to-Skill Mapping Reference

| Gap | Skill / Command |
|-----|----------------|
| No CLAUDE.md or outdated docs | `Skill(generating-agent-documentation)` |
| No justfile or inconsistent commands | `Skill(writing-justfiles)` |
| No pre-commit hooks or conventional commits | `Skill(setting-up-pre-commit)` |
| No PM integration | `Skill(configuring-project-management)` |
| Multiple foundation gaps | `/setup` |
| No tests or low coverage | `Skill(test-driven-development)` |
| Justfile missing test PATH param | `Skill(writing-justfiles)` |

## Agentic Engineering Readiness

### Can agents self-verify?
[assessment: can agents run quality checks independently with a single command? What commands exist?]

### Are feedback loops fast enough?
[assessment: estimated duration at each tier, bottlenecks identified]

### Are tests trustworthy?
[assessment: test reliability indicators - flaky tests, deterministic execution, clear pass/fail signals]

---

*Generated by Claude Code QA Review Skill v1.1.0*
```
