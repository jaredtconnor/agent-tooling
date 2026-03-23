#!/bin/bash
# Hook: Automatic Compound Engineering
# Captures lessons after significant code changes

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/jlange/AI-AUTOMATION}"

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool name from JSON
TOOL=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

# Tools that trigger lesson extraction
TRIGGER_TOOLS=(
    "Write"
    "Edit"
    "MultiEdit"
    "Task"
)

# Check if tool should trigger lesson extraction
for trigger in "${TRIGGER_TOOLS[@]}"; do
    if [[ "$TOOL" == "$trigger" ]]; then
        # Check if enough time has passed since last extraction (avoid spam)
        LAST_RUN_FILE="$PROJECT_DIR/.claude/hooks/.last-compound-run"
        CURRENT_TIME=$(date +%s)

        if [[ -f "$LAST_RUN_FILE" ]]; then
            LAST_RUN=$(cat "$LAST_RUN_FILE")
            TIME_DIFF=$((CURRENT_TIME - LAST_RUN))

            # Only run if more than 5 minutes have passed
            if [[ $TIME_DIFF -lt 300 ]]; then
                echo '{"action": "continue"}'
                exit 0
            fi
        fi

        # Update last run time
        mkdir -p "$PROJECT_DIR/.claude/hooks"
        echo "$CURRENT_TIME" > "$LAST_RUN_FILE"

        cat <<EOF
{
    "action": "queue_agent",
    "agent": "lesson-extractor",
    "message": "Capturing lessons from recent changes for compound engineering",
    "delay": 10,
    "priority": "low"
}
EOF
        exit 0
    fi
done

echo '{"action": "continue"}'
