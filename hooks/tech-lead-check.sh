#!/bin/bash
# Hook: Always use tech-lead-orchestrator for task coordination
# Runs on UserPromptSubmit to ensure tech-lead analyzes all tasks

# Read JSON input from stdin
INPUT=$(cat)

# Extract the prompt from JSON (if needed for analysis)
# PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')

# Always suggest tech-lead-orchestrator for task analysis and coordination
echo "📋 Suggesting tech-lead-orchestrator for optimal task coordination"

# Exit 0 to allow the prompt to continue
exit 0
