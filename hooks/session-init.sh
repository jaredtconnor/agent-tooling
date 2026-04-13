#!/usr/bin/env bash

# DLC Plugin - Session Initialization Script
# Surfaces workflow context and repository status on session start

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"

# =============================================================================
# Build Context Output
# =============================================================================

build_context() {
    cat << 'DLC_EOF'
# DLC Plugin

## Workflow

For features and code changes: `/dlc:refine` → `/dlc:plan` → `/dlc:breakdown` → `/dlc:execute` → `/dlc:pr`

Other commands: `/dlc:quick` (lightweight tasks), `/dlc:address-feedback` (PR feedback)

Always prefer `just` commands (`just test`, `just lint`, `just format`, `just build`). Run `just --list` to discover available recipes.
DLC_EOF
}

# =============================================================================
# Check Repository Initialization Status
# =============================================================================

check_repo_status() {
    local status=""

    if [ -f "$REPO_ROOT/CLAUDE.md" ]; then
        status="Repository initialized"
    else
        status="Repository NOT initialized - recommend running /foundations:setup"
    fi

    echo "$status"
}

build_foundations_context() {
    cat << 'FOUND_EOF'

## Repository Setup & Review (Foundations Plugin)

- `/foundations:setup` - Initialize repository with CLAUDE.md, justfile, pre-commit hooks, PM integration
- `/foundations:qa-review` - Assess repository QA readiness for agentic workflows
- `/foundations:cicd-review` - Review CI/CD pipeline quality and generate improvements
FOUND_EOF
}

# =============================================================================
# Build and Output JSON
# =============================================================================

CONTEXT_CONTENT=$(build_context)
REPO_STATUS=$(check_repo_status)
FOUNDATIONS_CONTEXT=$(build_foundations_context)

FULL_CONTEXT="${CONTEXT_CONTENT}${FOUNDATIONS_CONTEXT}
Repository Status: ${REPO_STATUS}"

jq -n --arg ctx "$FULL_CONTEXT" \
  '{
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: $ctx
    }
  }'

exit 0
