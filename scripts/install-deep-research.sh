#!/usr/bin/env bash
# Install the Deep Research skill pack under dr-* names for Claude Code and Codex.
# macOS/BSD sed assumed (darwin). Idempotent: safe to re-run.
set -euo pipefail

UPSTREAM="https://github.com/Weizhena/Deep-Research-skills.git"
CLAUDE_HOME="$HOME/.claude"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "==> Cloning $UPSTREAM"
git clone --depth 1 "$UPSTREAM" "$TMP/src"
SRC="$TMP/src"

# Copy one skill dir and namespace it: research* -> dr-research*
# $1 = source skill dir, $2 = destination skills root
install_skill() {
  local src_dir="$1" dest_root="$2"
  local base dest
  base="$(basename "$src_dir")"        # e.g. research-deep
  dest="$dest_root/dr-$base"           # e.g. .../dr-research-deep
  rm -rf "$dest"
  mkdir -p "$dest_root"
  cp -R "$src_dir" "$dest"
  sed -i '' -E 's/^name: research/name: dr-research/' "$dest/SKILL.md"
  sed -i '' 's#/research#/dr-research#g' "$dest/SKILL.md"
}

echo "==> Claude Code skills -> $CLAUDE_HOME/skills"
for d in "$SRC"/skills/research-en/*/; do
  install_skill "${d%/}" "$CLAUDE_HOME/skills"
done

echo "==> Claude Code web-search-agent -> $CLAUDE_HOME/agents"
mkdir -p "$CLAUDE_HOME/agents"
cp "$SRC/agents/web-search-agent.md" "$CLAUDE_HOME/agents/web-search-agent.md"
rm -rf "$CLAUDE_HOME/agents/web-search-modules"
cp -R "$SRC/agents/web-search-modules" "$CLAUDE_HOME/agents/web-search-modules"

echo "==> Codex skills -> $CODEX_HOME/skills"
for d in "$SRC"/skills/research-codex-en/*/; do
  install_skill "${d%/}" "$CODEX_HOME/skills"
done

echo "==> Codex web-researcher agent -> $CODEX_HOME/agents"
mkdir -p "$CODEX_HOME/agents"
cp "$SRC/agents-codex/web-researcher.toml" "$CODEX_HOME/agents/web-researcher.toml"
rm -rf "$CODEX_HOME/agents/web-search-modules"
cp -R "$SRC/agents-codex/web-search-modules" "$CODEX_HOME/agents/web-search-modules"

echo "==> Python dependency: pyyaml"
python3 -m pip install --quiet pyyaml \
  || python3 -m pip install --quiet --break-system-packages pyyaml

echo "==> Merging Codex config -> $CODEX_HOME/config.toml (additive, backs up .bak)"
CODEX_HOME="$CODEX_HOME" python3 - <<'PY'
import os, re, shutil
from pathlib import Path

cfg = Path(os.environ["CODEX_HOME"]) / "config.toml"
cfg.parent.mkdir(parents=True, exist_ok=True)
text = cfg.read_text(encoding="utf-8") if cfg.exists() else ""
if cfg.exists():
    shutil.copy(cfg, str(cfg) + ".bak")

# 1. top-level flag
if not re.search(r'(?m)^suppress_unstable_features_warning\s*=', text):
    text = "suppress_unstable_features_warning = true\n" + text

# 2. additive keys under [features] (preserve existing keys such as hooks/js_repl)
def ensure_section_keys(text, header, keys):
    m = re.search(rf'(?ms)^\[{re.escape(header)}\]\n(.*?)(?=^\[|\Z)', text)
    if m:
        body = m.group(1)
        add = "".join(f"{k} = {v}\n" for k, v in keys.items()
                      if not re.search(rf'(?m)^{re.escape(k)}\s*=', body))
        if add:
            text = text[:m.start(1)] + add + text[m.start(1):]
    else:
        block = f"[{header}]\n" + "".join(f"{k} = {v}\n" for k, v in keys.items())
        text = text.rstrip() + "\n\n" + block + "\n"
    return text

text = ensure_section_keys(text, "features",
                           {"multi_agent": "true",
                            "default_mode_request_user_input": "true"})

# 3. [agents.web_researcher]
if not re.search(r'(?ms)^\[agents\.web_researcher\]', text):
    desc = ("Use this agent when you need to research information on the internet, "
            "particularly for debugging issues, finding solutions to technical problems, "
            "or gathering comprehensive information from multiple sources. This agent excels "
            "at finding relevant discussions. Use when you need creative search strategies, "
            "thorough investigation, or compilation of findings from multiple sources.")
    block = ('[agents.web_researcher]\n'
             f'description = "{desc}"\n'
             'config_file = "agents/web-researcher.toml"\n')
    text = text.rstrip() + "\n\n" + block

cfg.write_text(text.rstrip() + "\n", encoding="utf-8")
print(f"Codex config updated: {cfg}")
PY

echo "==> Done. Restart Claude Code / Codex to pick up new skills."
