#!/usr/bin/env bash
set -euo pipefail

DEFAULT_AGENTS=(claude-code cursor codex)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/external-skills.json"

# Git Bash on Windows ships `python` with no `python3` alias.
PY_BIN="$(command -v python3 || command -v python || true)"
if [[ -z "$PY_BIN" ]]; then
  echo "install-agent-skills.sh: no python interpreter on PATH" >&2
  exit 1
fi

usage() {
  cat <<'USAGE'
Usage:
  install-agent-skills.sh --list-local              List skills shipped from this repo
  install-agent-skills.sh --list-external           List entries in external-skills.json
  install-agent-skills.sh --all                     Install every external manifest entry
  install-agent-skills.sh --name <name>             Install one manifest entry by name
  install-agent-skills.sh <owner/repo-or-url> [...] Ad-hoc install of any source

External installs go global for: claude-code, cursor, codex.
Local skills live under skills/ and are projected by this repo.
USAGE
}

# Print "<source>\t<skills-csv-or-empty>" for the requested manifest entries.
# Args: optional name filter (empty = all).
read_manifest() {
  local filter="${1:-}"
  "$PY_BIN" - "$MANIFEST" "$filter" <<'PY'
import json, sys
path, name_filter = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
sources = data.get("sources", [])
if name_filter:
    sources = [s for s in sources if s.get("name") == name_filter]
    if not sources:
        sys.stderr.write(f"no manifest entry named '{name_filter}'\n")
        sys.exit(3)
for s in sources:
    src = s.get("source")
    if not src:
        sys.stderr.write(f"manifest entry missing 'source': {s}\n")
        sys.exit(4)
    skills = s.get("skills") or []
    print(f"{s.get('name','')}\t{src}\t{','.join(skills)}")
PY
}

list_external() {
  "$PY_BIN" - "$MANIFEST" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
for s in data.get("sources", []):
    skills = s.get("skills")
    subset = f"  (subset: {', '.join(skills)})" if skills else ""
    print(f"- {s.get('name','?')}: {s.get('source','?')}{subset}")
    desc = s.get("description")
    if desc:
        print(f"    {desc}")
PY
}

install_source() {
  local source="$1"
  shift
  local cmd=(npx skills add "$source" --global --yes)
  for agent in "${DEFAULT_AGENTS[@]}"; do
    cmd+=(--agent "$agent")
  done
  cmd+=("$@")
  echo "+ ${cmd[*]}"
  "${cmd[@]}"
}

install_from_manifest() {
  local filter="${1:-}"
  while IFS=$'\t' read -r name source skills_csv; do
    [[ -z "$source" ]] && continue
    local extra=()
    if [[ -n "$skills_csv" ]]; then
      IFS=',' read -ra skill_arr <<<"$skills_csv"
      for s in "${skill_arr[@]}"; do
        extra+=(--skill "$s")
      done
    fi
    echo "==> $name ($source)"
    install_source "$source" "${extra[@]}"
  done < <(read_manifest "$filter")
}

if [[ $# -eq 0 ]]; then
  usage
  exit 2
fi

case "$1" in
  --list-local)
    npx skills add . --list
    ;;
  --list-external)
    list_external
    ;;
  --all)
    install_from_manifest ""
    ;;
  --name)
    [[ $# -ge 2 ]] || { usage; exit 2; }
    install_from_manifest "$2"
    ;;
  -h|--help)
    usage
    ;;
  *)
    source=$1
    shift
    install_source "$source" "$@"
    ;;
esac
