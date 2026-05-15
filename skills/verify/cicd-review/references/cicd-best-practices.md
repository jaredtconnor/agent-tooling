# CI/CD Best Practices Reference

Comprehensive reference for the CI/CD pipeline review skill. Defines each pillar, scoring criteria, detection patterns, hardening checklist, and the full report template.

---

## Pillar Definitions

### Pillar 1: Build

**Purpose:** Fast, cached, reproducible builds that minimise CI wait time and resource consumption.

**Detection patterns:**

| What | Glob / Grep |
|------|-------------|
| GitHub Actions cache | `grep -r 'actions/cache' .github/workflows/` |
| Setup actions with cache | `grep -r 'cache:' .github/workflows/` (for `actions/setup-node`, `actions/setup-python`, etc.) |
| Matrix builds | `grep -r 'strategy:' .github/workflows/` then check for `matrix:` |
| Concurrency groups | `grep -r 'concurrency:' .github/workflows/` |
| Timeouts | `grep -r 'timeout-minutes:' .github/workflows/` |
| Path filters | `grep -r 'paths:' .github/workflows/` or `grep -r 'paths-ignore:' .github/workflows/` |
| Build artifacts | `grep -r 'actions/upload-artifact' .github/workflows/` |
| Docker multi-stage | `grep -r 'FROM.*AS' Dockerfile*` |
| Shallow checkout | `grep -r 'fetch-depth' .github/workflows/` |
| Selective execution | `grep -r 'paths-filter\|dorny' .github/workflows/` |
| Docker layer cache | `grep -r 'buildx\|type=local\|type=gha' .github/workflows/` |
| Larger runners | `grep -r 'xl\|xlarge\|large' .github/workflows/` (in `runs-on:` context) — Team/Enterprise only, higher cost |

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No CI build configuration detected |
| 1-2 | Basic build step exists but no caching, no timeouts |
| 3-4 | Build with some caching OR concurrency, but not both |
| 5-6 | Caching + concurrency + timeouts + shallow checkout; builds complete in reasonable time |
| 7-8 | All of above + path filters + selective execution + matrix builds + artifacts; cache hit rates >70% |
| 9-10 | All of above + Docker layer caching + optimised parallelism + build times consistently <5min |

**Anti-patterns:**
- No caching — every build downloads dependencies from scratch
- Full git clone — `fetch-depth: 0` when full history isn't needed
- No timeouts — jobs can run indefinitely, consuming resources
- No concurrency — duplicate builds stack up on rapid pushes
- Building everything on every push — no path filters or selective execution

---

### Pillar 2: Integration & E2E Tests

**Purpose:** Comprehensive test execution in CI that catches integration issues, API contract violations, and user-facing regressions.

**Detection patterns:**

| What | Glob / Grep |
|------|-------------|
| Service containers | `grep -r 'services:' .github/workflows/` |
| Playwright | `grep -r 'playwright' .github/workflows/` or `Glob("playwright.config.*")` |
| Cypress | `grep -r 'cypress' .github/workflows/` or `Glob("cypress.config.*")` |
| Contract tests | `grep -r 'pact\|dredd\|contract' .github/workflows/` |
| Test reports | `grep -r 'actions/upload-artifact.*test' .github/workflows/` |
| Test sharding | `grep -r 'shard\|parallel\|split' .github/workflows/` |
| Docker Compose in CI | `grep -r 'docker-compose\|docker compose' .github/workflows/` |
| Test reporter | `grep -r 'test-reporter\|junit-report\|publish-test-results' .github/workflows/` |
| Job summary | `grep -r 'GITHUB_STEP_SUMMARY' .github/workflows/` |
| fail-fast: false | `grep -r 'fail-fast' .github/workflows/` |
| Flaky test retry | `grep -r 'retry\|rerun\|flaky' .github/workflows/` |

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No tests run in CI |
| 1-2 | Unit tests only in CI, no integration or E2E |
| 3-4 | Unit + some integration tests; no service containers or E2E |
| 5-6 | Unit + integration with service containers OR E2E tests present |
| 7-8 | All of above + test result reporting (PR annotations/check runs) + `fail-fast: false` + reasonable pass rates |
| 9-10 | All of above + contract tests + test sharding + flaky test management + <1% flaky test rate |

**Anti-patterns:**
- Unit tests only — no integration coverage catches interface bugs in production
- No service containers — integration tests mock everything, missing real issues
- No E2E — user-facing regressions only caught manually
- No test result reporting — failures only visible in raw logs, not surfaced as PR annotations
- `fail-fast: true` (default) — first failure cancels other matrix jobs, hiding additional failures
- Flaky tests ignored — failures become noise and are ignored

---

### Pillar 3: Static Analysis / Code Quality

**Purpose:** Automated code quality enforcement in CI that catches bugs, style violations, type errors, and complexity issues before review.

**Detection patterns:**

| What | Glob / Grep |
|------|-------------|
| ESLint | `grep -r 'eslint' .github/workflows/` |
| Ruff / Pylint | `grep -r 'ruff\|pylint' .github/workflows/` |
| Type checking | `grep -r 'tsc\|mypy\|pyright' .github/workflows/` |
| CodeQL | `grep -r 'codeql' .github/workflows/` or `Glob(".github/workflows/codeql*")` |
| Semgrep | `grep -r 'semgrep' .github/workflows/` |
| SonarQube | `grep -r 'sonar' .github/workflows/` |
| Coverage | `grep -r 'coverage\|codecov\|coveralls' .github/workflows/` |
| Coverage thresholds | Check tool configs for minimum coverage settings |
| PR annotations | `grep -r 'reviewdog\|--format github\|problem-matcher' .github/workflows/` |

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No static analysis in CI |
| 1-2 | Linter runs but results are advisory (don't block PR) |
| 3-4 | Linter blocks PRs; no type checking or coverage in CI |
| 5-6 | Linter + type checking in CI; coverage reported but no threshold |
| 7-8 | Linter + type checking + coverage with threshold + code scanning (CodeQL/Semgrep) |
| 9-10 | All of above + complexity analysis + all checks required status checks |

**Anti-patterns:**
- Advisory-only linting — findings are reported but don't block merges
- No type checking in CI — type errors caught locally but not enforced
- Coverage reported but no gate — coverage can decrease without notice
- Code scanning alerts ignored — accumulating unaddressed findings

---

### Pillar 4: Security Scanning

**Purpose:** Automated security checks that detect vulnerabilities, dependency risks, secret leaks, and supply chain threats in the CI pipeline.

**Detection patterns:**

| What | Glob / Grep |
|------|-------------|
| CodeQL SAST | `Glob(".github/workflows/codeql*")` |
| Semgrep | `grep -r 'semgrep' .github/workflows/` |
| Snyk | `grep -r 'snyk' .github/workflows/` |
| Dependabot | `Glob(".github/dependabot.yml")` |
| Renovate | `Glob("renovate.json")` or `Glob(".github/renovate.json")` |
| npm audit | `grep -r 'npm audit\|yarn audit' .github/workflows/` |
| pip-audit | `grep -r 'pip-audit' .github/workflows/` |
| Gitleaks | `grep -r 'gitleaks' .github/workflows/` or `.pre-commit-config.yaml` |
| TruffleHog | `grep -r 'trufflehog' .github/workflows/` |
| SHA-pinned actions | Check if actions use `@<40-char-sha>` vs `@v*` tags |
| Permissions | `grep -r 'permissions:' .github/workflows/` |
| OIDC | `grep -r 'id-token' .github/workflows/` |
| Dangerous patterns | `grep -r 'pull_request_target' .github/workflows/` |

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No security scanning in CI |
| 1-2 | Dependabot/Renovate configured but no SAST or secrets detection |
| 3-4 | Dependency scanning + some SAST; actions not SHA-pinned |
| 5-6 | SAST + dependency scanning + secrets detection; most actions SHA-pinned |
| 7-8 | All of above + minimal permissions + no dangerous patterns + environment-based deploys |
| 9-10 | All of above + OIDC + all actions SHA-pinned + 0 open critical alerts + security scanning required |

**Anti-patterns:**
- Actions pinned to tags not SHAs — vulnerable to tag-reassignment supply chain attacks (see tj-actions CVE-2025-30066)
- Overly permissive `permissions` — `contents: write` or worse when only `contents: read` needed
- `pull_request_target` with PR checkout — allows malicious PRs to execute arbitrary code with write permissions
- `${{ github.event.* }}` in `run:` blocks — script injection vulnerability
- Long-lived secrets for cloud access — should use OIDC instead
- Dependabot alerts accumulating — alerts exist but are not addressed

---

### Pillar 5: Agentic PR Review

**Purpose:** AI-assisted and automated review processes that complement human review, ensure consistent quality, and accelerate the review cycle.

**Detection patterns:**

| What | Glob / Grep |
|------|-------------|
| AI review tools | `grep -r 'claude\|copilot\|coderabbit\|codium\|sourcery' .github/workflows/` |
| CODEOWNERS | `Glob(".github/CODEOWNERS")` |
| PR templates | `Glob(".github/pull_request_template.md")` or `Glob(".github/PULL_REQUEST_TEMPLATE/*")` |
| Merge queue | `grep -r 'merge_group' .github/workflows/` |
| Auto-merge | `grep -r 'auto-merge\|merge-queue\|gh pr merge' .github/workflows/` |
| Review bot configs | `Glob(".github/copilot-review*")`, `Glob(".coderabbit*")` |

**Scoring criteria (0-10):**

| Score | Criteria |
|-------|----------|
| 0 | No automated review tooling, no PR template, no CODEOWNERS |
| 1-2 | PR template exists but no CODEOWNERS or automated review |
| 3-4 | PR template + CODEOWNERS; no AI review tooling |
| 5-6 | PR template + CODEOWNERS + required human reviewers (branch protection) |
| 7-8 | All of above + AI review tool configured and active |
| 9-10 | All of above + merge queue + auto-merge for dependency updates + review metrics tracked |

**Anti-patterns:**
- No PR template — PRs lack context, making review harder
- No CODEOWNERS — no automatic reviewer assignment
- No required reviewers — PRs can merge without any review
- AI tools configured but results ignored — noise without value

---

## GitHub Actions Hardening Checklist

Use this checklist during Phase 7 (Security) assessment. Each item is pass/fail.

| # | Check | How to Detect | Risk |
|---|-------|---------------|------|
| 1 | SHA-pinned actions | All `uses:` lines reference `@<sha>` not `@v*` | Supply chain — tag reassignment |
| 2 | Minimal permissions | `permissions: {}` at workflow level, scoped per-job | Privilege escalation |
| 3 | No `pull_request_target` with checkout | `pull_request_target` trigger without `actions/checkout` of PR head | Arbitrary code execution |
| 4 | No script injection | No `${{ github.event.* }}` directly in `run:` blocks | Command injection |
| 5 | OIDC for cloud auth | `id-token: write` + cloud provider OIDC config | Credential theft from long-lived secrets |
| 6 | Environment-based deploys | Production deployments use `environment:` with protection rules | Unauthorised deployments |
| 7 | Concurrency groups | `concurrency:` set on workflows to prevent duplicate runs | Resource waste, race conditions |
| 8 | Timeouts | `timeout-minutes:` set on all jobs | Runaway jobs consuming resources |
| 9 | Secrets not in logs | No `echo ${{ secrets.* }}` or similar | Secret exposure |
| 10 | Dependabot/Renovate active | `.github/dependabot.yml` or `renovate.json` exists | Outdated vulnerable dependencies |

---

## Detection Patterns Quick Reference

Compact catalog of CI/CD-specific file globs and grep patterns for rapid scanning.

### CI Platform Files

| Platform | Glob |
|----------|------|
| GitHub Actions | `.github/workflows/*.yml`, `.github/workflows/*.yaml` |
| Jenkins | `Jenkinsfile`, `Jenkinsfile.*` |
| CircleCI | `.circleci/config.yml` |
| GitLab CI | `.gitlab-ci.yml` |
| Azure DevOps | `azure-pipelines.yml`, `.azure-pipelines/*.yml` |
| Bitbucket | `bitbucket-pipelines.yml` |

### GitHub-Specific Files

| File | Purpose |
|------|---------|
| `.github/CODEOWNERS` | Automatic reviewer assignment |
| `.github/pull_request_template.md` | PR description template |
| `.github/PULL_REQUEST_TEMPLATE/*.md` | Multiple PR templates |
| `.github/dependabot.yml` | Dependency update automation |
| `.github/actions/*/action.yml` | Composite actions |

### Security Tool Configs

| Tool | Config Files |
|------|-------------|
| Gitleaks | `.gitleaks.toml`, `gitleaks.toml` |
| Semgrep | `.semgrep.yml`, `.semgrep/` |
| CodeQL | `.github/codeql/`, `codeql-config.yml` |
| Snyk | `.snyk` |
| Trivy | `trivy.yaml`, `.trivy.yaml` |

---

## GitHub CLI Commands

Commands for Phase 3 (Review GitHub Context). All require `gh` CLI authenticated to the repository.

```bash
# Get owner/repo and default branch
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)

# Recent workflow runs (pass/fail rates, durations)
gh run list --limit 20

# Recent failures (flaky tests, recurring issues)
gh run list --status failure --limit 10

# Recent merged PRs (review patterns)
gh pr list --state merged --limit 10

# Cache utilisation
gh api "repos/${REPO}/actions/cache/usage"

# Branch protection rules
gh api "repos/${REPO}/branches/${DEFAULT_BRANCH}/protection"

# Configured secrets (names only, never values)
gh secret list

# Open Dependabot alert count
gh api "repos/${REPO}/dependabot/alerts" --jq 'length'

# Open code scanning alert count
gh api "repos/${REPO}/code-scanning/alerts" --jq 'length'
```

**Graceful degradation:** If any command fails (permissions, not a GitHub repo, `gh` not installed), skip that data point and note it in the report. Never let a failed `gh` command block the review.

---

## Example Snippets

Brief best-practice YAML snippets for common improvements.

### Dependency Caching (Node.js)

```yaml
- uses: actions/setup-node@<sha>
  with:
    node-version-file: '.node-version'
    cache: 'npm'
```

### Minimal Permissions

```yaml
permissions: {}

jobs:
  build:
    permissions:
      contents: read
    runs-on: ubuntu-latest
```

### Concurrency Group

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### OIDC for AWS

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: aws-actions/configure-aws-credentials@<sha>
    with:
      role-to-assume: arn:aws:iam::123456789012:role/deploy
      aws-region: us-east-1
```

### Path Filters

```yaml
on:
  push:
    paths:
      - 'src/**'
      - 'package.json'
      - 'package-lock.json'
    paths-ignore:
      - '*.md'
      - 'docs/**'
```

### Selective Execution with paths-filter

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.filter.outputs.backend }}
      frontend: ${{ steps.filter.outputs.frontend }}
    steps:
      - uses: dorny/paths-filter@<sha>
        id: filter
        with:
          filters: |
            backend:
              - 'src/api/**'
              - 'src/models/**'
            frontend:
              - 'src/components/**'
              - 'src/pages/**'

  backend-tests:
    needs: changes
    if: ${{ needs.changes.outputs.backend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - run: npm run test:backend
```

### Test Result Reporting

```yaml
- uses: dorny/test-reporter@<sha>
  if: always()
  with:
    name: Test Results
    path: 'reports/junit.xml'
    reporter: java-junit
```

### Service Containers (PostgreSQL)

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: test
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

---

## Gap-to-Action Mapping

**Pipeline gaps** → `Task(platform-engineer)` with a description of what to implement:
- No CI pipeline, caching, concurrency, path filters, timeouts, service containers, E2E, linting, type checking, coverage, CodeQL/SAST, dependency scanning, secrets detection, CODEOWNERS, PR template, AI review
- Performance: shallow checkout, selective execution (`dorny/paths-filter`), larger runners, Docker layer caching
- Feedback quality: test result reporting (`dorny/test-reporter`), PR annotations, `fail-fast: false`, job summaries, flaky test management
- SHA-pinning, minimal permissions, OIDC — all security hardening tasks

**Foundation gaps** → foundations skills:
- No pre-commit hooks → `Skill(setting-up-pre-commit)`
- No justfile → `Skill(writing-justfiles)`
- No CLAUDE.md → `Skill(generating-agent-documentation)`
- Multiple gaps → `/setup`

**Manual actions:**
- Branch protection → configure in GitHub repository settings

---

## Report Template

Use this template when generating the CI/CD Pipeline Review report.

```markdown
# CI/CD Pipeline Review

**Repository:** [repo name]
**Date:** [date]
**CI Platform:** [detected platform(s)]
**Overall Score:** [X.X / 10]
**Maturity Level:** [Mature / Developing / Immature]

---

## Executive Summary

[2-3 sentence summary of pipeline maturity, primary strengths, and critical gaps]

**Primary constraint:** [The single most impactful gap limiting pipeline quality]

---

## Pillar Assessment

| Pillar | Score | Status | Summary |
|--------|-------|--------|---------|
| 1. Build | X/10 | [Strong/Moderate/Weak] | [One-line summary] |
| 2. Integration & E2E Tests | X/10 | [Strong/Moderate/Weak] | [One-line summary] |
| 3. Static Analysis | X/10 | [Strong/Moderate/Weak] | [One-line summary] |
| 4. Security Scanning | X/10 | [Strong/Moderate/Weak] | [One-line summary] |
| 5. Agentic PR Review | X/10 | [Strong/Moderate/Weak] | [One-line summary] |

---

## Live Pipeline Data

> If `gh` CLI data was unavailable, note: "Live data unavailable — scoring based on static config analysis only."

| Metric | Value |
|--------|-------|
| Run pass rate / Avg duration | X% (Y/Z runs) / Xm Xs |
| Recent failure pattern | [Most common failure type] |
| Cache utilisation | X bytes active |
| Dependabot / Code scanning alerts | X / X open |
| Branch protection | [Enabled/Disabled] — [X required reviewers] — [required checks list] |

---

## Pillar-by-Pillar Detail

> For each pillar (1-5): **Detected** (list), **Missing** (list), **Live data insights** (if available).
> Pillar 4 includes the hardening checklist from the Hardening Checklist section above.

## Workflow Hygiene

Reusable workflows, job dependencies (`needs`), trigger hygiene, naming conventions.

## Recommendations

**Critical** → Build or Security gaps below 4. **Important** → Efficiency/coverage gaps. **Nice-to-Have** → DX improvements.

## Next Steps

[Top 3 prioritised actions with specific commands/skills to run]
```
