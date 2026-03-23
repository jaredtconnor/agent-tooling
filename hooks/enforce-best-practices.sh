#!/bin/bash
# Claude Code Hook: Enforce Best Practices
# Automatically ensures best practices are followed after tool usage

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/jlange/AI-AUTOMATION}"

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool name from JSON using simple grep/sed (since jq might not be installed)
TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

# Function to check if we've made significant changes
significant_changes() {
    local tool="$1"
    case "$tool" in
        "Write"|"Edit"|"MultiEdit")
            return 0
            ;;
        "Task")
            # Check if Task agent made changes
            if [[ -n "$CLAUDE_FILE_PATHS" ]]; then
                return 0
            fi
            ;;
    esac
    return 1
}

# Main enforcement logic
if significant_changes "$TOOL_NAME"; then
    # Check if we need to run E2E tests
    if [[ -f "$PROJECT_DIR/tests/e2e/run_e2e_test.sh" ]]; then
        cat <<EOF
{
    "action": "notify",
    "message": "Significant changes detected. Consider running E2E tests: ./tests/e2e/run_e2e_test.sh",
    "priority": "medium"
}
EOF
    fi

    # Check if code formatting is needed
    if [[ -n "$CLAUDE_FILE_PATHS" ]]; then
        for file_path in $CLAUDE_FILE_PATHS; do
            if [[ "$file_path" =~ \.(py|js|ts|tsx)$ ]]; then
                cat <<EOF
{
    "action": "suggest",
    "message": "Code files modified. Consider running formatters (ruff, prettier) if needed.",
    "priority": "low"
}
EOF
                break
            fi
        done
    fi
else
    echo '{"action": "continue"}'
fi

exit 0
