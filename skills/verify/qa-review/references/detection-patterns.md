# Detection Patterns Catalog

Comprehensive catalog of file patterns, grep patterns, and config locations for detecting QA infrastructure. Organized by category. Use with glob and grep tools during repository scanning.

---

## Test Files

Patterns to detect test files across languages and frameworks.

| Language | Glob Patterns |
|----------|--------------|
| JavaScript/TypeScript | `**/*.test.{js,ts,jsx,tsx}`, `**/*.spec.{js,ts,jsx,tsx}`, `**/__tests__/**` |
| Python | `**/test_*.py`, `**/*_test.py`, `**/tests/**/*.py`, `**/conftest.py` |
| Go | `**/*_test.go` |
| Rust | `**/tests/**/*.rs` (integration), inline `#[cfg(test)]` modules |
| Java/Kotlin | `**/*Test.java`, `**/*Tests.java`, `**/*Spec.java`, `**/*Test.kt` |
| Ruby | `**/spec/**/*_spec.rb`, `**/test/**/*_test.rb` |
| PHP | `**/*Test.php`, `**/tests/**/*.php` |
| C#/.NET | `**/*Tests.cs`, `**/*Test.cs`, `**/Tests/**/*.cs` |
| Elixir | `**/test/**/*_test.exs` |

**Grep pattern for test count estimation:**

```
rg -c '(describe|it|test|def test_|func Test|#\[test\]|@Test|@pytest)' --type-add 'testfiles:*.{test,spec}.{js,ts,jsx,tsx}' -t testfiles
```

---

## Test Framework Configs

| Framework | Config Files |
|-----------|-------------|
| Jest | `jest.config.{js,ts,cjs,mjs}`, `jest.config.json`, `package.json` (`jest` key) |
| Vitest | `vitest.config.{js,ts,mts}`, `vite.config.*` (with test section) |
| Mocha | `.mocharc.{yml,yaml,json,js,cjs}` |
| Pytest | `pytest.ini`, `pyproject.toml` (`[tool.pytest]`), `setup.cfg` (`[tool:pytest]`), `conftest.py` |
| Go test | Built-in, no config. Detect via `*_test.go` files |
| Cargo test | Built-in, no config. Detect via `#[cfg(test)]` or `tests/` dir |
| JUnit | `**/src/test/**`, Maven/Gradle test configs |
| RSpec | `.rspec`, `spec/spec_helper.rb` |
| PHPUnit | `phpunit.xml`, `phpunit.xml.dist` |
| xUnit/.NET | `*.csproj` with `xunit` or `nunit` package references |
| ExUnit | `test/test_helper.exs` |
| Playwright | `playwright.config.{js,ts}` |
| Cypress | `cypress.config.{js,ts,cjs,mjs}`, `cypress.json` |
| WebdriverIO | `wdio.conf.{js,ts}` |

---

## CI/CD Configs

| Platform | Config Files | Triggers to Check |
|----------|-------------|-------------------|
| GitHub Actions | `.github/workflows/*.yml` | `on: push`, `on: pull_request`, `on: merge_group` |
| Jenkins | `Jenkinsfile`, `jenkins/*.groovy` | Pipeline stages |
| CircleCI | `.circleci/config.yml` | `workflows` section |
| GitLab CI | `.gitlab-ci.yml` | `rules`, `only/except` |
| Azure Pipelines | `azure-pipelines.yml`, `.azure-pipelines/*.yml` | `trigger`, `pr` sections |
| Bitbucket Pipelines | `bitbucket-pipelines.yml` | `pipelines.pull-requests`, `pipelines.branches` |
| Travis CI | `.travis.yml` | `branches`, `script` |
| Buildkite | `.buildkite/pipeline.yml` | `steps` |

**Grep pattern for required status checks:**

```
rg -l '(required_status_checks|branch-protection|status.check|required.*review)' .github/
```

---

## Pre-commit Hooks

| Tool | Config Files |
|------|-------------|
| pre-commit | `.pre-commit-config.yaml` |
| Husky | `.husky/*`, `.husky/pre-commit`, `package.json` (`husky` key) |
| lefthook | `lefthook.yml`, `.lefthook.yml` |
| lint-staged | `.lintstagedrc*`, `package.json` (`lint-staged` key) |
| Git hooks (raw) | `.git/hooks/pre-commit`, `.githooks/*` |
| Overcommit | `.overcommit.yml` |

**Grep pattern for hook content:**

```
rg '(pre-commit|pre-push|commit-msg)' .pre-commit-config.yaml .husky/ lefthook.yml 2>/dev/null
```

---

## Linting & Formatting

| Tool | Config Files | Language |
|------|-------------|----------|
| ESLint | `.eslintrc*`, `eslint.config.{js,mjs,cjs,ts}`, `package.json` (`eslintConfig`) | JS/TS |
| Prettier | `.prettierrc*`, `prettier.config.*` | JS/TS/CSS/MD |
| Biome | `biome.json`, `biome.jsonc` | JS/TS |
| Ruff | `ruff.toml`, `pyproject.toml` (`[tool.ruff]`) | Python |
| Pylint | `.pylintrc`, `pyproject.toml` (`[tool.pylint]`) | Python |
| Flake8 | `.flake8`, `setup.cfg` (`[flake8]`), `tox.ini` (`[flake8]`) | Python |
| Black | `pyproject.toml` (`[tool.black]`) | Python |
| isort | `pyproject.toml` (`[tool.isort]`), `.isort.cfg` | Python |
| golangci-lint | `.golangci.yml`, `.golangci.yaml` | Go |
| Clippy | (part of Cargo, check CI for `cargo clippy`) | Rust |
| rustfmt | `rustfmt.toml`, `.rustfmt.toml` | Rust |
| RuboCop | `.rubocop.yml` | Ruby |
| PHP CS Fixer | `.php-cs-fixer.php`, `.php-cs-fixer.dist.php` | PHP |
| ktlint | `.editorconfig`, Gradle plugin | Kotlin |
| Checkstyle | `checkstyle.xml`, Maven/Gradle plugin | Java |
| Deno | `deno.json`, `deno.jsonc` | JS/TS (Deno) |

---

## Type Checking

| Tool | Config Files | Key Settings to Check |
|------|-------------|----------------------|
| TypeScript | `tsconfig.json`, `tsconfig.*.json` | `strict`, `noImplicitAny`, `strictNullChecks` |
| Mypy | `mypy.ini`, `pyproject.toml` (`[tool.mypy]`), `setup.cfg` (`[mypy]`) | `strict`, `disallow_untyped_defs` |
| Pyright | `pyrightconfig.json`, `pyproject.toml` (`[tool.pyright]`) | `typeCheckingMode` |
| Flow | `.flowconfig` | Type coverage |

**Grep pattern for TypeScript strictness:**

```
rg '"strict"\s*:\s*true' tsconfig.json
```

---

## Build & Task Runners

| Runner | Config Files | Key Entries to Check |
|--------|-------------|---------------------|
| just | `justfile`, `.justfile`, `Justfile` | `test`, `lint`, `format`, `build`, `check` recipes |
| Make | `Makefile`, `GNUmakefile` | `test`, `lint`, `format`, `build` targets |
| npm/yarn/pnpm scripts | `package.json` (`scripts` section) | `test`, `lint`, `format`, `build`, `check` |
| tox | `tox.ini` | `[testenv]` environments, `commands` |
| nox | `noxfile.py` | Session definitions |
| Taskfile | `Taskfile.yml`, `Taskfile.yaml` | `tasks` section |
| Rake | `Rakefile` | `test`, `lint`, `spec` tasks |
| Gradle | `build.gradle`, `build.gradle.kts` | `test`, `check`, `lint` tasks |
| Maven | `pom.xml` | `surefire-plugin`, `failsafe-plugin` |
| Cargo | `Cargo.toml` | Built-in `cargo test`, `cargo clippy` |
| Deno | `deno.json` | `tasks` section |

**Grep pattern for testing abstractions quality:**

```
rg '(just test|make test|npm test|yarn test|pnpm test|cargo test|go test|pytest|rake test)' justfile Makefile package.json 2>/dev/null
```

---

## Acceptance & BDD

| Category | Patterns |
|----------|----------|
| Gherkin feature files | `**/*.feature` |
| Cucumber configs | `cucumber.js`, `cucumber.yml`, `.cucumber.rc` |
| Behave (Python) | `features/*.feature`, `features/steps/*.py`, `behave.ini` |
| SpecFlow (.NET) | `*.feature`, `specflow.json` |
| GIVEN/WHEN/THEN in code | Grep: `(Given|When|Then|Scenario|Feature:)` in test files |
| Behavior-focused naming | Grep: `(should |it\(|describe\(|context\()` in test files |
| AAA pattern markers | Grep: `(Arrange|Act|Assert|# Given|# When|# Then)` in test files |

---

## Coverage

| Tool | Config Files |
|------|-------------|
| Istanbul/nyc | `.nycrc`, `.nycrc.json`, `nyc` key in `package.json` |
| Jest coverage | `jest.config.*` (`coverageThreshold`, `collectCoverage`) |
| Vitest coverage | `vitest.config.*` (`coverage` section) |
| coverage.py | `.coveragerc`, `pyproject.toml` (`[tool.coverage]`), `setup.cfg` (`[coverage:run]`) |
| Go cover | CI steps with `go test -cover` |
| Codecov | `codecov.yml`, `.codecov.yml` |
| Coveralls | `.coveralls.yml` |
| Cobertura | `cobertura.xml` output references in CI |
| SonarQube | `sonar-project.properties` |

**Grep pattern for coverage thresholds:**

```
rg '(coverageThreshold|fail_under|minimum.coverage|--cov-fail-under)' . -g '*.{json,toml,ini,yml,yaml,cfg}'
```

---

## Security Scanning

| Category | Config Files |
|----------|-------------|
| Snyk | `.snyk`, `.snyk.json` |
| Trivy | `.trivyignore`, `trivy.yaml` |
| Dependabot | `.github/dependabot.yml`, `dependabot.yml` |
| Renovate | `renovate.json`, `renovate.json5`, `.renovaterc`, `.renovaterc.json` |
| Gitleaks | `.gitleaks.toml` |
| detect-secrets | `.secrets.baseline` |
| secretlint | `.secretlintrc*` |
| Semgrep | `.semgrep.yml`, `.semgrep/` |
| CodeQL | `.github/codeql/`, `.github/workflows/codeql*.yml` |
| OWASP ZAP | `zap-*` configs in CI |
| Bandit (Python) | `.bandit`, `bandit.yaml`, `pyproject.toml` (`[tool.bandit]`) |
| Brakeman (Ruby) | `brakeman.yml` |
| Safety (Python) | `.safety-policy.yml` |

**Grep pattern for security steps in CI:**

```
rg -l '(snyk|trivy|codeql|semgrep|gitleaks|bandit|brakeman|safety|dependabot|renovate)' .github/workflows/ 2>/dev/null
```

---

## Contract Testing

| Tool | Config Files |
|------|-------------|
| Pact | `pact*.json`, `pact*.js`, `pact*.ts`, `**/pacts/**` |
| OpenAPI | `openapi*.{yml,yaml,json}`, `swagger*.{yml,yaml,json}` |
| JSON Schema | `**/*.schema.json` |
| gRPC/Protobuf | `**/*.proto`, `buf.yaml` |
| GraphQL schema | `**/*.graphql`, `**/*.gql` |
| AsyncAPI | `asyncapi*.{yml,yaml,json}` |

---

## Performance Testing

| Tool | Config Files |
|------|-------------|
| k6 | `k6*.js`, `k6*.ts`, `**/k6/**` |
| Locust | `locustfile*.py`, `**/locust/**` |
| JMeter | `**/*.jmx` |
| Artillery | `artillery*.yml`, `artillery*.yaml` |
| Gatling | `**/gatling/**`, `**/*Simulation.scala` |
| wrk/wrk2 | wrk scripts in CI or `bench/` |
| Benchmark files | `bench/`, `benchmarks/`, `perf/`, `*_bench_test.go`, `bench_*.py`, `*.bench.ts` |
| Lighthouse CI | `.lighthouserc.*`, `lighthouserc.*` |

---

## Mutation Testing

| Tool | Config Files |
|------|-------------|
| Stryker | `stryker.conf.{js,mjs,cjs,json}`, `.stryker-tmp/` |
| mutmut | `pyproject.toml` (`[tool.mutmut]`), `setup.cfg` (`[mutmut]`) |
| PIT (pitest) | Maven/Gradle plugin config (`pitest`) |
| cargo-mutants | Cargo subcommand (check CI for `cargo mutants`) |
| infection (PHP) | `infection.json`, `infection.json.dist` |

---

## Static Analysis

| Tool | Config Files |
|------|-------------|
| SonarQube | `sonar-project.properties`, `.sonarcloud.properties` |
| CodeClimate | `.codeclimate.yml` |
| Semgrep | `.semgrep.yml`, `.semgrep/` |
| PMD | `pmd-ruleset.xml`, Maven/Gradle plugin |
| SpotBugs | Maven/Gradle plugin, `spotbugs-exclude.xml` |
| Cppcheck | CI steps with `cppcheck` |
| ShellCheck | CI steps with `shellcheck`, `.shellcheckrc` |
| hadolint | `.hadolint.yaml`, CI steps for Dockerfile linting |

---

## Quick Detection Script

Run this sequence to rapidly detect QA infrastructure:

```bash
# 1. Test files
fd -e test.js -e test.ts -e spec.js -e spec.ts -e _test.go -e Test.java --type f | wc -l
fd test_ -e py --type f | wc -l

# 2. CI configs
fd -g '.github/workflows/*.yml' -g 'Jenkinsfile' -g '.circleci' -g '.gitlab-ci.yml'

# 3. Pre-commit
fd -g '.pre-commit-config.yaml' -g '.husky' -g 'lefthook.yml'

# 4. Linting
fd -g '.eslintrc*' -g 'eslint.config*' -g 'ruff.toml' -g '.golangci*' -g 'biome.json'

# 5. Type checking
fd -g 'tsconfig.json' -g 'mypy.ini' -g 'pyrightconfig.json'

# 6. Task runners
fd -g 'justfile' -g 'Makefile' -g 'Taskfile.yml' -g 'tox.ini' -g 'noxfile.py'

# 7. Coverage
fd -g '.coveragerc' -g 'codecov.yml' -g '.nycrc*'

# 8. Security
fd -g 'dependabot.yml' -g 'renovate.json*' -g '.snyk' -g '.gitleaks.toml' -g '.trivyignore'

# 9. E2E frameworks
fd -g 'playwright.config*' -g 'cypress.config*' -g 'wdio.conf*'

# 10. Performance
fd -g 'k6*' -g 'locustfile*' -g '*.jmx' -g 'artillery*'

# 11. BDD/Acceptance
fd -e feature --type f | wc -l

# 12. Contract testing
fd -g 'openapi*' -g 'swagger*' -g '*.proto' -g 'pact*'
```
