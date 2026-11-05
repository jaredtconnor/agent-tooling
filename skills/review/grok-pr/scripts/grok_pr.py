#!/usr/bin/env python3
"""Render a PR guide (guide.json + unified diff) into one interactive HTML page.

Usage:
  python grok_pr.py hunks <pr.diff>
  python grok_pr.py render <guide.json> <pr.diff> [--out index.html] [--no-open]

`hunks` prints the hunk IDs (`path#N`) that guide chapters reference.
`render` validates the guide against the diff, writes the page next to the
guide (or to --out) and opens it in the default browser.

Standard library only. Exit 2 means the guide has errors; they are listed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_DIR / "assets" / "template.html"
CANVAS = SKILL_DIR / "assets" / "canvas.json"
DATA_TOKEN = "__PR_GUIDE_DATA__"

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@ ?(.*)$")
GIT_HEADER_RE = re.compile(r"^diff --git a/(.*) b/(.*)$")

SEVERITIES = ("blocker", "major", "minor", "nit")
CATEGORIES = ("correctness", "syntax", "performance", "design", "tests", "security", "scope", "docs")
CANVAS_STATUSES = ("pass", "concern", "fail", "na", "unchecked")


def read_text(path: Path) -> str:
    """Read a diff or JSON file; Windows PowerShell 5 redirection writes UTF-16."""
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def unquote_path(p: str) -> str:
    # git C-quotes paths containing non-ASCII or control characters.
    if len(p) >= 2 and p[0] == '"' and p[-1] == '"':
        return p[1:-1].encode("latin-1", "backslashreplace").decode("unicode_escape").encode("latin-1").decode("utf-8", "replace")
    return p


def header_path(p: str) -> str | None:
    p = unquote_path(p.split("\t")[0].rstrip())
    if p == "/dev/null":
        return None
    return p[2:] if p.startswith(("a/", "b/")) else p


def parse_diff(text: str) -> list[dict]:
    files: list[dict] = []
    cur: dict | None = None
    hunk: dict | None = None
    old_left = new_left = 0
    old_no = new_no = 0

    for line in text.splitlines():
        if hunk is not None and (old_left > 0 or new_left > 0):
            tag = line[:1]
            body = line[1:]
            if tag == "\\":  # "\ No newline at end of file"
                continue
            if tag == "+":
                hunk["lines"].append(["+", None, new_no, body])
                new_no += 1
                new_left -= 1
                hunk["add"] += 1
            elif tag == "-":
                hunk["lines"].append(["-", old_no, None, body])
                old_no += 1
                old_left -= 1
                hunk["del"] += 1
            else:  # context; an empty line is context with its leading space stripped
                hunk["lines"].append([" ", old_no, new_no, body])
                old_no += 1
                new_no += 1
                old_left -= 1
                new_left -= 1
            continue

        if line.startswith("diff --git "):
            cur = {"path": None, "oldPath": None, "status": "modified", "binary": False, "hunks": []}
            files.append(cur)
            hunk = None
            m = GIT_HEADER_RE.match(line)
            if m:
                cur["oldPath"], cur["path"] = unquote_path(m.group(1)), unquote_path(m.group(2))
            continue
        if cur is None:
            continue

        m = HUNK_RE.match(line)
        if m:
            old_start, old_len, new_start, new_len, ctx = m.groups()
            old_left = 1 if old_len is None else int(old_len)
            new_left = 1 if new_len is None else int(new_len)
            old_no, new_no = int(old_start), int(new_start)
            hunk = {
                "oldStart": old_no, "oldLines": old_left,
                "newStart": new_no, "newLines": new_left,
                "ctx": ctx.strip(), "add": 0, "del": 0, "lines": [],
            }
            cur["hunks"].append(hunk)
            continue

        if hunk is not None:
            continue  # trailing noise after a complete hunk
        if line.startswith("new file mode"):
            cur["status"] = "added"
        elif line.startswith("deleted file mode"):
            cur["status"] = "deleted"
        elif line.startswith("rename from "):
            cur["oldPath"] = line[len("rename from "):]
            cur["status"] = "renamed"
        elif line.startswith("rename to "):
            cur["path"] = line[len("rename to "):]
            cur["status"] = "renamed"
        elif line.startswith("Binary files ") or line == "GIT binary patch":
            cur["binary"] = True
        elif line.startswith("--- "):
            p = header_path(line[4:])
            if p:
                cur["oldPath"] = p
        elif line.startswith("+++ "):
            p = header_path(line[4:])
            if p:
                cur["path"] = p

    for f in files:
        if f["status"] == "deleted" or not f["path"]:
            f["path"] = f["oldPath"]
        f["add"] = sum(h["add"] for h in f["hunks"])
        f["del"] = sum(h["del"] for h in f["hunks"])
        for i, h in enumerate(f["hunks"]):
            h["id"] = f"{f['path']}#{i}"
    return files


def first_change(hunk: dict) -> str:
    for t, _, _, s in hunk["lines"]:
        if t != " " and s.strip():
            return f"{t} {s.strip()}"[:90]
    return ""


def cmd_hunks(diff_path: Path) -> int:
    files = parse_diff(read_text(diff_path))
    if not files:
        print(f"no files found in {diff_path}; is it a unified git diff?", file=sys.stderr)
        return 2
    for f in files:
        extra = " binary" if f["binary"] else ""
        print(f"{f['path']}  ({f['status']}{extra}, +{f['add']} -{f['del']})")
        for h in f["hunks"]:
            span = f"@@ -{h['oldStart']},{h['oldLines']} +{h['newStart']},{h['newLines']} @@"
            print(f"  {h['id']}  {span}  +{h['add']} -{h['del']}  {first_change(h)}")
    return 0


def in_hunk(hunk: dict, line: int, side: str) -> bool:
    if side == "old":
        return hunk["oldStart"] <= line < hunk["oldStart"] + max(hunk["oldLines"], 1)
    return hunk["newStart"] <= line < hunk["newStart"] + max(hunk["newLines"], 1)


def build(guide: dict, files: list[dict]) -> tuple[dict, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    by_path = {f["path"]: f for f in files}
    hunk_ids = {h["id"]: f for f in files for h in f["hunks"]}

    for key in ("title", "tldr", "chapters"):
        if not guide.get(key):
            errors.append(f"missing required field: {key}")
    chapters = guide.get("chapters") or []
    if not isinstance(chapters, list):
        errors.append("chapters must be a list")
        chapters = []

    covered: set[str] = set()
    for ci, ch in enumerate(chapters):
        if not ch.get("title"):
            errors.append(f"chapters[{ci}] is missing title")
        refs: dict[str, list[str]] = {}
        for ref in ch.get("hunks") or []:
            if ref in hunk_ids:
                refs.setdefault(hunk_ids[ref]["path"], []).append(ref)
            elif ref in by_path:
                f = by_path[ref]
                refs.setdefault(ref, []).extend(h["id"] for h in f["hunks"])
                covered.add(ref)
            else:
                errors.append(f"chapters[{ci}] references unknown hunk or file: {ref}")
        for path, ids in refs.items():
            for hid in ids:
                if hid in covered:
                    warnings.append(f"{hid} appears in more than one chapter")
                covered.add(hid)
        ch["refs"] = [{"path": p, "hunks": list(dict.fromkeys(ids))} for p, ids in refs.items()]

    uncovered: dict[str, list[str]] = {}
    for f in files:
        ids = [h["id"] for h in f["hunks"] if h["id"] not in covered]
        if ids or (not f["hunks"] and f["path"] not in covered):
            uncovered[f["path"]] = ids
    if uncovered:
        n = sum(max(len(v), 1) for v in uncovered.values())
        warnings.append(f"{n} hunk(s) not in any chapter; added an 'Other changes' chapter: " + ", ".join(uncovered))
        chapters.append({
            "title": "Other changes",
            "summary": "The guide does not narrate these changes.",
            "auto": True,
            "refs": [{"path": p, "hunks": ids} for p, ids in uncovered.items()],
        })
    guide["chapters"] = chapters

    for fi, f in enumerate(guide.get("findings") or []):
        f["id"] = f"f{fi}"
        f.setdefault("side", "new")
        if f.get("severity") not in SEVERITIES:
            errors.append(f"findings[{fi}].severity must be one of {SEVERITIES}")
        if f.get("category") not in CATEGORIES:
            errors.append(f"findings[{fi}].category must be one of {CATEGORIES}")
        if not f.get("title"):
            errors.append(f"findings[{fi}] is missing title")
        path, line = f.get("path"), f.get("line")
        f["chapter"] = None
        if path and path not in by_path:
            warnings.append(f"findings[{fi}] path is not in the diff: {path}")
            continue
        for ci, ch in enumerate(chapters):
            ref = next((r for r in ch["refs"] if r["path"] == path), None)
            if not ref:
                continue
            if f["chapter"] is None:
                f["chapter"] = ci
            if isinstance(line, int) and any(
                in_hunk(h, line, f["side"]) for h in by_path[path]["hunks"] if h["id"] in ref["hunks"]
            ):
                f["chapter"] = ci
                break

    canvas_def = json.loads(read_text(CANVAS))
    item_ids = {i["id"] for c in canvas_def["categories"] for i in c["items"]}
    for key, val in (guide.get("canvas") or {}).items():
        if key not in item_ids:
            warnings.append(f"canvas item is not defined in assets/canvas.json: {key}")
        if not isinstance(val, dict) or val.get("status") not in CANVAS_STATUSES:
            errors.append(f"canvas.{key}.status must be one of {CANVAS_STATUSES}")

    guide.setdefault("id", guide.get("url") or guide.get("title"))
    data = {
        "guide": guide,
        "files": files,
        "canvas": canvas_def,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    return data, errors, warnings


def cmd_render(guide_path: Path, diff_path: Path, out: Path | None, open_browser: bool) -> int:
    try:
        guide = json.loads(read_text(guide_path))
    except json.JSONDecodeError as exc:
        print(f"ERROR: {guide_path} is invalid JSON: {exc}", file=sys.stderr)
        return 2
    files = parse_diff(read_text(diff_path))
    if not files:
        print(f"ERROR: no files found in {diff_path}; is it a unified git diff?", file=sys.stderr)
        return 2

    data, errors, warnings = build(guide, files)
    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2

    # "<" escaped so diff content cannot close the <script> element.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = read_text(TEMPLATE).replace(DATA_TOKEN, payload, 1)
    out = out or guide_path.with_name("index.html")
    out.write_text(html, encoding="utf-8")
    print(out.resolve())
    if open_browser:
        webbrowser.open(out.resolve().as_uri())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_h = sub.add_parser("hunks", help="list hunk IDs in a diff")
    p_h.add_argument("diff", type=Path)
    p_r = sub.add_parser("render", help="render guide.json + diff to HTML")
    p_r.add_argument("guide", type=Path)
    p_r.add_argument("diff", type=Path)
    p_r.add_argument("--out", type=Path)
    p_r.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    if args.cmd == "hunks":
        return cmd_hunks(args.diff)
    return cmd_render(args.guide, args.diff, args.out, not args.no_open)


if __name__ == "__main__":
    sys.exit(main())
