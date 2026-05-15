# Agent Tooling
# Common commands for local skills, Claude plugin metadata, and skills.sh installs.

set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
	@just --list

# List local skills discovered by the skills CLI
list:
	npx skills add . --list

# Alias for list
list-local: list

# Install an external skills package for Claude Code, Cursor, and Codex
install source *args:
	bash scripts/install-agent-skills.sh "{{source}}" {{args}}

# Install Vercel's public agent skill pack for the default agents
install-vercel:
	bash scripts/install-agent-skills.sh vercel-labs/agent-skills

# Create or repair runtime links from .agents/ into installed agents
link:
	npx @iannuttall/dotagents

# Validate Claude Code plugin metadata and local assets
plugin-check: verify
	@echo "Claude plugin install:"
	@echo "  /plugin marketplace add jaredtconnor/agent-tooling"
	@echo "  /plugin install agent-tooling@jared-agent-tooling"

# Validate local metadata and skill discovery
verify:
	python3 scripts/validate-agent-tooling.py
	npx skills add . --list >/dev/null

# Show the current repo changes
status:
	git status --short
