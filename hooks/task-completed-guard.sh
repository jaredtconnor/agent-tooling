#!/usr/bin/env bash
# task-completed-guard.sh - TaskCompleted hook for Agent Teams
#
# Fires when a task is being marked as completed.
# Exit 0 = allow completion, Exit 2 = block completion (stderr fed back as feedback).
#
# TaskCompleted does NOT support matchers or JSON decision control.

set -euo pipefail

# Consume stdin (required by hook protocol)
cat > /dev/null

# Allow task completion — Tier 3 skills handle TDD and code review gates.
# To enforce quality gates, add checks here and exit 2 with stderr feedback.

exit 0
