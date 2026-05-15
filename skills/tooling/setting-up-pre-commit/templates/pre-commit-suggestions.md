# Pre-commit Hook Suggestions

This document provides recommended pre-commit hooks based on detected project tooling.

## Essential Hooks (Always Recommended)

### 1. Conventional Commits

**Hook:** `conventional-pre-commit`
**Purpose:** Enforces consistent commit message format
**Why:** Enables automated changelog generation, semantic versioning, and clear commit history

```yaml
- repo: https://github.com/compilerla/conventional-pre-commit
  rev: v3.6.0
  hooks:
    - id: conventional-pre-commit
      stages: [commit-msg]
```

### 2. General File Checks

**Hooks:** `pre-commit-hooks`
**Purpose:** Catches common mistakes (trailing whitespace, merge conflicts, large files, secrets)
**Why:** Prevents accidental commits of problematic content

```yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v5.0.0
  hooks:
    - id: trailing-whitespace
    - id: end-of-file-fixer
    - id: check-yaml
    - id: check-json
    - id: check-added-large-files
    - id: check-merge-conflict
    - id: detect-private-key
```

## Language-Specific Hooks

### Python Projects

If using **Ruff** (recommended):

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.8.4
  hooks:
    - id: ruff
      args: [--fix]
    - id: ruff-format
```

If using **mypy** for type checking:

```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.14.0
  hooks:
    - id: mypy
      additional_dependencies: [types-all]
```

If using **Black** (if not using Ruff):

```yaml
- repo: https://github.com/psf/black
  rev: 24.10.0
  hooks:
    - id: black
```

### TypeScript/JavaScript Projects

**ESLint:**

```yaml
- repo: https://github.com/pre-commit/mirrors-eslint
  rev: v9.17.0
  hooks:
    - id: eslint
      files: \.(js|ts|jsx|tsx)$
      types: [file]
      additional_dependencies:
        - eslint@9.17.0
        - typescript@5.7.2
```

**Prettier:**

```yaml
- repo: https://github.com/pre-commit/mirrors-prettier
  rev: v4.0.0-alpha.8
  hooks:
    - id: prettier
      types_or: [css, javascript, jsx, ts, tsx, json, markdown, yaml]
```

### Go Projects

```yaml
- repo: https://github.com/golangci/golangci-lint
  rev: v1.62.2
  hooks:
    - id: golangci-lint

- repo: https://github.com/dnephin/pre-commit-golang
  rev: v0.5.1
  hooks:
    - id: go-fmt
    - id: go-vet
    - id: go-mod-tidy
```

### Rust Projects

```yaml
- repo: https://github.com/doublify/pre-commit-rust
  rev: v1.0
  hooks:
    - id: fmt
    - id: clippy
      args: ['--', '-D', 'warnings']
```

## Security Hooks (Recommended for All Projects)

### Secret Detection

**Prevents accidentally committing secrets:**

```yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
```

First run: `detect-secrets scan > .secrets.baseline`

### TruffleHog (Advanced Secret Scanning)

```yaml
- repo: https://github.com/trufflesecurity/trufflehog
  rev: v3.86.2
  hooks:
    - id: trufflehog
      args: [git, 'file://.', --only-verified, --fail]
```

## Optional Hooks by Use Case

### If Using Docker

```yaml
- repo: https://github.com/hadolint/hadolint
  rev: v2.13.1-beta
  hooks:
    - id: hadolint-docker
```

### If Using Terraform

```yaml
- repo: https://github.com/antonbabenko/pre-commit-terraform
  rev: v1.96.2
  hooks:
    - id: terraform_fmt
    - id: terraform_validate
    - id: terraform_tflint
```

### If Writing Shell Scripts

```yaml
- repo: https://github.com/shellcheck-py/shellcheck-py
  rev: v0.10.0.1
  hooks:
    - id: shellcheck
```

### If Writing Markdown Documentation

```yaml
- repo: https://github.com/igorshubovych/markdownlint-cli
  rev: v0.42.0
  hooks:
    - id: markdownlint
      args: [--fix]
```

### If Using SQL

```yaml
- repo: https://github.com/sqlfluff/sqlfluff
  rev: 3.3.0
  hooks:
    - id: sqlfluff-lint
    - id: sqlfluff-fix
```

## How to Choose

**Start minimal:**

1. Conventional commits (always)
2. General file checks (always)
3. Language-specific linters (for your languages)

**Then add based on needs:**

- Secret scanning (if handling sensitive data)
- Docker linting (if using Docker)
- Security scanning (for production applications)
- Additional formatters (if needed)

**Don't:**

- Add everything at once
- Add hooks you don't need
- Slow down commits unnecessarily

## Installation

After creating `.pre-commit-config.yaml`:

```bash
# Install pre-commit
pip install pre-commit
# or
brew install pre-commit

# Install the git hooks
pre-commit install --install-hooks

# Test on all files
pre-commit run --all-files
```

## Justfile Integration

Add to your justfile:

```justfile
# Install pre-commit hooks
pre-commit-install:
    pre-commit install --install-hooks

# Run pre-commit on all files
pre-commit-run:
    pre-commit run --all-files

# Update pre-commit hooks to latest versions
pre-commit-update:
    pre-commit autoupdate
```
