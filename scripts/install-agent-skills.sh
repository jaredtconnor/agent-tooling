#!/usr/bin/env bash
set -euo pipefail

DEFAULT_AGENTS=(claude-code cursor codex)

if [[ "${1:-}" == "--list-local" ]]; then
  npx skills add . --list
  exit 0
fi

if [[ $# -eq 0 ]]; then
  cat <<'USAGE'
Usage:
  bash scripts/install-agent-skills.sh --list-local
  bash scripts/install-agent-skills.sh <owner/repo-or-url> [--skill <name> ...]

Installs external skills globally for the default agents:
  claude-code, cursor, codex

Local skills are sourced from skills/ and can be installed from this agent
tooling repo; do not install this repo into itself.
USAGE
  exit 2
fi

source=$1
shift

cmd=(npx skills add "$source" --global --yes)
for agent in "${DEFAULT_AGENTS[@]}"; do
  cmd+=(--agent "$agent")
done
cmd+=("$@")

"${cmd[@]}"
