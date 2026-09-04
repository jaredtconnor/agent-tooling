#!/usr/bin/env bash
# Publication gate for agent-tooling: block publication on any secret or
# privacy-policy violation. Runs full-history secret scanning plus a content
# and path policy for private overlays, work identity, and private endpoints.
#
# Usage:
#   scripts/verify-publication.sh [target-dir]   # default: repo root
#
# Exit 0 only when the target is safe to publish. Any finding exits non-zero.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
TARGET="${1:-$REPO_ROOT}"
POLICY="$HERE/publication-policy.txt"
# Optional, git-ignored local denylist for values too private to commit to a
# public repo (e.g. the private Forgejo host). Merged when present.
LOCAL_POLICY="$HERE/publication-policy.local.txt"
ALLOWLIST="$HERE/publication-allowlist.txt"
# The policy definition files legitimately contain patterns/examples; never scan
# them as if they were source content.
is_policy_file() {
  case "$1" in
    scripts/publication-policy.txt|scripts/publication-policy.local.txt|scripts/publication-allowlist.txt) return 0 ;;
    *) return 1 ;;
  esac
}

fail=0
note() { printf '%s\n' "$*" >&2; }

# --- 1. secrets (gitleaks) -----------------------------------------------
if command -v gitleaks >/dev/null 2>&1; then
  if [ -d "$TARGET/.git" ]; then
    gitleaks git "$TARGET" --no-banner >/dev/null 2>&1 \
      || { note "FAIL secrets: gitleaks found findings in history"; fail=1; }
  else
    gitleaks dir "$TARGET" --no-banner >/dev/null 2>&1 \
      || { note "FAIL secrets: gitleaks found findings in files"; fail=1; }
  fi
else
  note "error: gitleaks is required"; exit 2
fi

# --- file list to scan ----------------------------------------------------
# Tracked files when the target is a git repo; otherwise all files under it.
if [ -d "$TARGET/.git" ]; then
  mapfile -t FILES < <(git -C "$TARGET" ls-files)
  prefix="$TARGET/"
else
  mapfile -t FILES < <(cd "$TARGET" && find . -type f -not -path './.git/*' | sed 's#^\./##')
  prefix="$TARGET/"
fi

# --- 2. content policy ----------------------------------------------------
allow_res=()
if [ -f "$ALLOWLIST" ]; then
  while IFS= read -r a; do
    [ -z "$a" ] && continue
    case "$a" in \#*) continue ;; esac
    allow_res+=("$a")
  done < "$ALLOWLIST"
fi

patterns=()
for pf in "$POLICY" "$LOCAL_POLICY"; do
  [ -f "$pf" ] || continue
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    case "$p" in \#*) continue ;; esac
    patterns+=("$p")
  done < "$pf"
done

# A matching line is a violation unless it also matches an allowlist pattern.
line_allowed() {
  local line="$1" re
  for re in "${allow_res[@]}"; do
    printf '%s' "$line" | grep -IEq "$re" && return 0
  done
  return 1
}

for pat in "${patterns[@]}"; do
  for f in "${FILES[@]}"; do
    is_policy_file "$f" && continue
    [ -f "$prefix$f" ] || continue
    while IFS= read -r hit; do
      [ -z "$hit" ] && continue
      local_line="${hit#*:}"
      if ! line_allowed "$local_line"; then
        note "FAIL policy: '$f:${hit%%:*}' matches prohibited pattern /$pat/"
        fail=1
      fi
    done < <(grep -IEn "$pat" "$prefix$f" 2>/dev/null)
  done
done

# --- 3. private-overlay path convention ----------------------------------
# Private overlays are additive and never belong in the public source tree.
for f in "${FILES[@]}"; do
  case "$f" in
    private/*|*/private/*|private_*|*/private_*|*.private.*)
      note "FAIL overlay: '$f' is a private-overlay path and must not be public"
      fail=1 ;;
  esac
done

if [ "$fail" -eq 0 ]; then
  note "publication policy: OK ($TARGET)"
fi
exit "$fail"
