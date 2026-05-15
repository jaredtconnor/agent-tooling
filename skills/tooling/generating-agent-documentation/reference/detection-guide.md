# Technology Stack Detection Guide

Quick reference for detecting project tooling and technologies.

## Language Detection

```bash
# Find primary languages
find . -maxdepth 3 -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" | head -5
```

## Python Tooling

```bash
# Check for Python projects
ls pyproject.toml requirements.txt setup.py 2>/dev/null

# Detect Python tooling
grep -E "ruff|black|mypy|flake8|pytest" pyproject.toml 2>/dev/null

# Check Python version
grep -E "python.*=|requires-python" pyproject.toml 2>/dev/null
```

## TypeScript/JavaScript Tooling

```bash
# Check for Node projects
ls package.json tsconfig.json .eslintrc* .prettierrc* 2>/dev/null

# Detect tooling
jq '.scripts,.devDependencies' package.json 2>/dev/null | grep -E "eslint|prettier|vitest|jest"
```

## Go Tooling

```bash
ls go.mod go.sum 2>/dev/null
```

## Rust Tooling

```bash
ls Cargo.toml Cargo.lock 2>/dev/null
```

## Infrastructure

```bash
# Docker
ls Dockerfile docker-compose.yml 2>/dev/null

# Terraform
find . -maxdepth 2 -name "*.tf" | head -1

# Kubernetes
find . -maxdepth 2 -name "*.yaml" -o -name "*.yml" | xargs grep -l "kind:" 2>/dev/null | head -3
```

## Build Tools

```bash
# Check for justfile
ls justfile Justfile 2>/dev/null

# Check for Makefile
ls Makefile makefile 2>/dev/null
```

## Monorepo Indicators

```bash
# Check for monorepo tools
ls lerna.json nx.json pnpm-workspace.yaml turbo.json 2>/dev/null

# Check for workspace structure
ls -d packages/ apps/ 2>/dev/null
```
