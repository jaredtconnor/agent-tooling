#!/bin/bash
# Hook: Memory Bank Synchronization
# Automatically syncs memory bank when files get too large

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/jlange/AI-AUTOMATION}"

# Check memory file sizes
check_memory_sizes() {
    local total_size=0
    local needs_sync=false

    for file in "$PROJECT_DIR"/CLAUDE-{decisions,lessons,patterns,troubleshooting}.md; do
        if [[ -f "$file" ]]; then
            size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
            total_size=$((total_size + size))

            # If any single file > 50K, needs sync
            if [[ $size -gt 51200 ]]; then
                needs_sync=true
            fi
        fi
    done

    # If total > 150K, needs sync
    if [[ $total_size -gt 153600 ]]; then
        needs_sync=true
    fi

    if [[ "$needs_sync" == "true" ]]; then
        cat <<EOF
{
    "action": "notify",
    "message": "Memory bank files are growing large ($(($total_size / 1024))K). Consider running memory-bank-synchronizer.",
    "agent": "memory-bank-synchronizer",
    "priority": "medium"
}
EOF
    else
        echo '{"action": "continue"}'
    fi
}

check_memory_sizes
