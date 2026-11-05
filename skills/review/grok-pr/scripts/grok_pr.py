#!/usr/bin/env python3
"""Render a PR guide (guide.json + unified diff) into one interactive HTML page.

Usage:
  python grok_pr.py hunks <pr.diff>
  python grok_pr.py render <guide.json> <pr.diff> [--repo DIR --ref REF] [--out index.html] [--no-open]
  python grok_pr.py serve <workdir> [--port N] [--no-open]
  python grok_pr.py post <workdir> [--dry-run]
  python grok_pr.py fixes <workdir>
  python grok_pr.py config [--repo DIR]
  python grok_pr.py threads <pr-url> [--all]

`hunks` prints the hunk IDs (`path#N`) that guide chapters reference.
`render` validates the guide against the diff, writes the page next to the
guide (or to --out) and opens it in the default browser. With --repo, findings
whose line is outside the diff get the surrounding source from `git show REF:path`.
`serve` serves the rendered page on localhost and saves accept/skip/edit
decisions to <workdir>/decisions.json; in review mode the page can post them.
`post` creates a pending GitHub review from the accepted items: review comments in
review mode, thread replies in respond mode.
`fixes` prints the accepted items as a fix list for the agent (self and respond modes).
`config` prints the effective scrutiny settings.
`threads` prints a PR's unresolved review threads and review bodies (input for respond mode).

Standard library only. Exit 2 means the guide has errors; they are listed.
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_DIR / "assets" / "template.html"
CANVAS = SKILL_DIR / "assets" / "canvas.json"
DATA_TOKEN = "__PR_GUIDE_DATA__"

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@ ?(.*)$")
GIT_HEADER_RE = re.compile(r"^diff --git a/(.*) b/(.*)$")

SEVERITIES = ("blocker", "major", "minor", "nit")
CATEGORIES = ("correctness", "syntax", "performance", "design", "tests", "security", "scope", "standards", "docs")
MODES = ("review", "self", "respond")
ASSESSMENTS = ("agree", "partly", "disagree", "question")

# Scrutiny presets. minSeverity: lowest severity the agent reports, and below it findings
# start skipped; autoAccept: severities that start accepted. Config may override either.
CONFIG_PATH = Path.home() / ".config" / "grok-pr" / "config.json"
REPO_CONFIG = ".grok-pr.json"
PRESETS = {
    "light": {"minSeverity": "major", "autoAccept": ["blocker", "major"]},
    "standard": {"minSeverity": "minor", "autoAccept": ["blocker", "major"]},
    "strict": {"minSeverity": "nit", "autoAccept": []},
}
DEFAULT_SCRUTINY = "light"
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
    if guide.setdefault("mode", "review") not in MODES:
        errors.append(f"mode must be one of {MODES}")
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
        if guide["mode"] == "respond":
            if not isinstance(f.get("reply"), str) or not f["reply"].strip():
                errors.append(f"findings[{fi}] needs a reply in respond mode")
            if f.get("assessment") not in ASSESSMENTS:
                errors.append(f"findings[{fi}].assessment must be one of {ASSESSMENTS}")
        path, line = f.get("path"), f.get("line")
        f["chapter"] = None
        p = f.get("proposal")
        if p is not None:
            if not isinstance(p, dict) or not isinstance(p.get("code"), str) or not p["code"].strip():
                errors.append(f"findings[{fi}].proposal needs a non-empty code string")
            elif "replaces" in p and not (
                isinstance(p["replaces"], list) and len(p["replaces"]) == 2
                and all(isinstance(n, int) for n in p["replaces"]) and 0 < p["replaces"][0] <= p["replaces"][1]
            ):
                errors.append(f"findings[{fi}].proposal.replaces must be [start, end] line numbers on the new side")
        # inDiff: the finding renders inline in a diff hunk; otherwise the page lists it under
        # "Findings outside the diff" with a source excerpt when one is available.
        f["inDiff"] = bool(
            path in by_path and isinstance(line, int)
            and any(in_hunk(h, line, f["side"]) for h in by_path[path]["hunks"])
        )
        if path and path not in by_path:
            warnings.append(f"findings[{fi}] is in a file the diff does not touch ({path}); listed under 'Findings outside the diff'")
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


EXCERPT_CONTEXT = 8


def attach_source(findings: list[dict], files: list[dict], repo: Path | None, ref: str) -> list[str]:
    """Attach source lines the page cannot get from the diff.

    - `excerpt`: lines around a finding that is not on a changed line (needs --repo).
    - `proposal.before`: the current lines a proposal replaces, from the repo when given,
      else from the diff when every line in the range is inside a hunk.
    """
    warnings: list[str] = []
    cache: dict[str, list[str] | None] = {}
    by_path = {f["path"]: f for f in files}

    def repo_lines(path: str) -> list[str] | None:
        if repo is None:
            return None
        if path not in cache:
            res = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"], capture_output=True)
            if res.returncode:
                warnings.append(f"no source for {path} at {ref}: {res.stderr.decode('utf-8', 'replace').strip()}")
                cache[path] = None
            else:
                cache[path] = res.stdout.decode("utf-8-sig", "replace").splitlines()
        return cache[path]

    def diff_lines(path: str, start: int, end: int) -> list[str] | None:
        f = by_path.get(path)
        if not f:
            return None
        new = {n: s for h in f["hunks"] for t, _, n, s in h["lines"] if n is not None}
        return [new[n] for n in range(start, end + 1)] if all(n in new for n in range(start, end + 1)) else None

    for f in findings:
        path, line = f.get("path"), f.get("line")
        if repo and path and isinstance(line, int) and not f["inDiff"] and f["side"] == "new":
            lines = repo_lines(path)
            if lines and line > len(lines):
                warnings.append(f"{f['id']} line {line} is past the end of {path} at {ref} ({len(lines)} lines)")
            elif lines:
                start = max(1, line - EXCERPT_CONTEXT)
                f["excerpt"] = {"start": start, "lines": lines[start - 1:line + EXCERPT_CONTEXT]}

        p = f.get("proposal")
        if not p or "replaces" not in p or not path:
            continue
        start, end = p["replaces"]
        lines = repo_lines(path)
        before = lines[start - 1:end] if lines and end <= len(lines) else diff_lines(path, start, end)
        if before is None:
            warnings.append(f"{f['id']} proposal.replaces {start}-{end} in {path} is not in the diff; pass --repo/--ref to show the current code")
        else:
            p["before"] = {"start": start, "lines": before}
    return warnings


def cmd_render(guide_path: Path, diff_path: Path, out: Path | None, open_browser: bool,
               repo: Path | None = None, ref: str = "HEAD") -> int:
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
    try:
        data["config"] = load_config(repo)
    except ConfigError as exc:
        errors.append(str(exc))
    if not errors:
        warnings += attach_source(data["guide"].get("findings") or [], files, repo, ref)
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


class ConfigError(Exception):
    pass


def load_config(repo: Path | None) -> dict:
    """User config, then the repo's .grok-pr.json on top, then the chosen preset filled in."""
    raw: dict = {}
    sources: list[str] = []
    for p in [CONFIG_PATH] + ([repo / REPO_CONFIG] if repo else []):
        if p.is_file():
            try:
                raw.update(json.loads(read_text(p)))
            except json.JSONDecodeError as exc:
                raise ConfigError(f"{p} is invalid JSON: {exc}") from exc
            sources.append(str(p))
    scrutiny = raw.get("scrutiny", DEFAULT_SCRUTINY)
    if scrutiny not in PRESETS:
        raise ConfigError(f"scrutiny must be one of {tuple(PRESETS)}, got {scrutiny!r}")
    cfg = {"scrutiny": scrutiny, **PRESETS[scrutiny]}
    cfg.update({k: raw[k] for k in ("minSeverity", "autoAccept") if k in raw})
    if cfg["minSeverity"] not in SEVERITIES or not all(s in SEVERITIES for s in cfg["autoAccept"]):
        raise ConfigError(f"minSeverity and autoAccept must use {SEVERITIES}")
    cfg["sources"] = sources
    return cfg


def default_status(item: dict, cfg: dict) -> str:
    """Mirrors defaultStatus() in template.html."""
    if item["id"] == "summary" or item["severity"] in cfg["autoAccept"]:
        return "accepted"
    return "skipped" if SEVERITIES.index(item["severity"]) > SEVERITIES.index(cfg["minSeverity"]) else "pending"


def load_work(work: Path) -> tuple[dict, list[dict], dict]:
    """Rebuild the guide from <workdir>/guide.json + pr.diff so finding ids match the page."""
    guide = json.loads(read_text(work / "guide.json"))
    files = parse_diff(read_text(work / "pr.diff"))
    data, errors, _ = build(guide, files)
    if errors:
        raise ConfigError("guide.json has errors; run render first: " + "; ".join(errors))
    return data["guide"], files, load_decisions(work)


def load_decisions(work: Path) -> dict:
    p = work / "decisions.json"
    return json.loads(read_text(p)) if p.is_file() else {"decisions": {}, "posted": []}


def save_decisions(work: Path, state: dict) -> None:
    (work / "decisions.json").write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def page_config(work: Path) -> dict:
    """The config the page was rendered with, so CLI defaults match what the page showed."""
    index = work / "index.html"
    if index.is_file():
        m = re.search(r'id="pr-data">(.*?)</script>', read_text(index), re.S)
        if m:
            cfg = json.loads(m.group(1)).get("config")
            if cfg:
                return cfg
    return load_config(None)


def compose_body(f: dict) -> str:
    """Fallback text for a finding the page never saved a body for."""
    parts = [f.get("detail", "").strip(), f.get("suggestion", "").strip()]
    p = f.get("proposal")
    if p:
        parts.append("```\n" + p["code"].rstrip("\n") + "\n```")
        parts.append(p.get("note", "").strip())
    return "\n\n".join(x for x in parts if x)


def accepted_items(guide: dict, state: dict, cfg: dict) -> list[tuple[dict, str]]:
    """(item, body) for every accepted item not yet posted; the review summary comes first."""
    posted = {i for rec in state.get("posted", []) for i in rec["ids"]}
    items = ([{"id": "summary", "severity": "major", "title": "Review summary", "detail": guide["reviewBody"]}]
             if guide.get("reviewBody") else []) + (guide.get("findings") or [])
    out = []
    for it in items:
        d = state["decisions"].get(it["id"], {})
        if it["id"] in posted or d.get("status", default_status(it, cfg)) != "accepted":
            continue
        if d.get("body"):
            body = d["body"]
        else:
            body = f"{it['reply']}" if guide["mode"] == "respond" and it["id"] != "summary" else compose_body(it)
        out.append((it, body))
    return out


def fix_text(it: dict, mode: str, body: str) -> str:
    """What the agent should change. In respond mode the posted text is a reply, so use the fix fields."""
    if mode != "respond" or it["id"] == "summary":
        return body
    quote = "\n".join("> " + s for s in (it.get("quote") or "").strip().splitlines())
    return "\n\n".join(x for x in [quote, compose_body(it)] if x)


def cmd_fixes(work: Path) -> int:
    guide, _, state = load_work(work)
    items = accepted_items(guide, state, page_config(work))
    if not items:
        print("No accepted findings.")
        return 0
    print(f"# Fixes for {guide['title']}\n")
    print("Fix each item in the working tree following the repo's AGENTS.md and coding standards. "
          "Keep each change minimal, run the tests that cover it, and report fixed or declined with the reason.\n")
    for n, (it, body) in enumerate(items, 1):
        loc = f" `{it['path']}:{it['line']}`" if it.get("path") and it.get("line") else ""
        sev = "root cause" if it["id"] == "summary" else f"{it['severity']} · {it['category']}"
        print(f"## {n}. [{it['id']}] {it['title']} ({sev}){loc}\n")
        print(fix_text(it, guide["mode"], body).strip() + "\n")
    return 0


class PostError(Exception):
    pass


def gh(args: list[str], stdin: str | None = None) -> str:
    res = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, encoding="utf-8")
    if res.returncode:
        raise PostError(f"gh {' '.join(args[:3])} failed: {(res.stderr or res.stdout).strip()}")
    return res.stdout


def graphql(query: str, variables: dict) -> dict:
    out = json.loads(gh(["api", "graphql", "--input", "-"], json.dumps({"query": query, "variables": variables})))
    if out.get("errors"):
        raise PostError("GraphQL: " + "; ".join(e.get("message", "?") for e in out["errors"]))
    return out["data"]


def record_post(work: Path, review_id: str, url: str, ids: list[str]) -> dict:
    record = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "reviewId": review_id, "url": url, "ids": ids}
    state = load_decisions(work)  # re-read: the page may have saved since load_work
    state.setdefault("posted", []).append(record)
    save_decisions(work, state)
    return record


ADD_REVIEW = """mutation($pr: ID!, $body: String) {
  addPullRequestReview(input: {pullRequestId: $pr, body: $body}) { pullRequestReview { id } } }"""
ADD_REPLY = """mutation($review: ID!, $thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewId: $review, pullRequestReviewThreadId: $thread, body: $body}) {
    comment { id } } }"""


def post_replies(work: Path, owner: str, repo: str, num: str, items: list[tuple[dict, str]], dry_run: bool) -> dict:
    """Respond mode: one pending review holding a reply on each accepted thread; replies to
    review-level feedback (no thread) go in the review body under a quote of what they answer."""
    threaded, top = [], []
    for it, body in items:
        if it.get("thread"):
            threaded.append((it, body.strip()))
        else:
            quote = "\n".join("> " + s for s in (it.get("quote") or "").strip().splitlines()[:6])
            top.append("\n\n".join(x for x in [quote, body.strip()] if x))
    review_body = "\n\n---\n\n".join(top)
    url = f"https://github.com/{owner}/{repo}/pull/{num}"
    result = {"replies": len(threaded), "inBody": len(top), "url": url}
    if dry_run:
        return {**result, "body": review_body, "threads": [{"thread": it["thread"], "body": b} for it, b in threaded]}

    pr_id = json.loads(gh(["api", f"repos/{owner}/{repo}/pulls/{num}"]))["node_id"]
    review_id = graphql(ADD_REVIEW, {"pr": pr_id, "body": review_body or None})["addPullRequestReview"]["pullRequestReview"]["id"]
    done = [it["id"] for it, _ in items if not it.get("thread")]
    try:
        for it, body in threaded:
            graphql(ADD_REPLY, {"review": review_id, "thread": it["thread"], "body": body})
            done.append(it["id"])
    finally:
        record = record_post(work, review_id, url, done)  # keep partial progress so nothing posts twice
    return {**result, "record": record}


THREADS = """query($owner: String!, $repo: String!, $num: Int!) {
  repository(owner: $owner, name: $repo) { pullRequest(number: $num) {
    reviewThreads(first: 100) { nodes { id isResolved isOutdated path line originalLine diffSide
      comments(first: 50) { nodes { databaseId author { login } body url createdAt } } } }
    reviews(first: 50) { nodes { databaseId author { login } state body url submittedAt } } } } }"""


def cmd_threads(url: str, include_resolved: bool) -> int:
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        print("ERROR: expected https://github.com/<owner>/<repo>/pull/<n>", file=sys.stderr)
        return 1
    owner, repo, num = m.groups()
    try:
        pr = graphql(THREADS, {"owner": owner, "repo": repo, "num": int(num)})["repository"]["pullRequest"]
    except PostError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    threads = [{
        "thread": t["id"], "path": t["path"], "line": t["line"] or t["originalLine"],
        "side": "old" if t["diffSide"] == "LEFT" else "new", "outdated": t["isOutdated"], "resolved": t["isResolved"],
        "comments": [{"author": (c["author"] or {}).get("login"), "body": c["body"], "url": c["url"], "at": c["createdAt"]}
                     for c in t["comments"]["nodes"]],
    } for t in pr["reviewThreads"]["nodes"] if include_resolved or not t["isResolved"]]
    reviews = [{"author": (r["author"] or {}).get("login"), "state": r["state"], "body": r["body"], "url": r["url"]}
               for r in pr["reviews"]["nodes"] if r["body"].strip()]
    print(json.dumps({"threads": threads, "reviews": reviews}, indent=2, ensure_ascii=False))
    return 0


def post_review(work: Path, dry_run: bool = False) -> dict:
    """Create one pending review: inline comments for findings on diff lines, the rest in the body."""
    guide, files, state = load_work(work)
    if guide["mode"] == "self":
        raise PostError("this guide is a self-review; use `fixes` instead of posting")
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", guide.get("url") or "")
    if not m:
        raise PostError("guide.url must be a https://github.com/<owner>/<repo>/pull/<n> URL")
    owner, repo, num = m.groups()
    items = accepted_items(guide, state, page_config(work))
    if not items:
        raise PostError("nothing accepted to post")
    if guide["mode"] == "respond":
        return post_replies(work, owner, repo, num, items, dry_run)

    # Line numbers come from pr.diff; refuse if the PR has moved on since the guide was built.
    current = parse_diff(gh(["pr", "diff", num, "-R", f"{owner}/{repo}", "--color=never"]))
    if current != files:
        raise PostError("the PR changed since this guide was built; re-run the review before posting")
    head = json.loads(gh(["api", f"repos/{owner}/{repo}/pulls/{num}"]))["head"]["sha"]

    summary, inline, in_body = "", [], []
    for it, body in items:
        if it["id"] == "summary":
            summary = body.strip()
        elif it.get("inDiff"):
            inline.append({"path": it["path"], "line": it["line"],
                           "side": "LEFT" if it["side"] == "old" else "RIGHT", "body": body.strip()})
        else:
            loc = f"`{it['path']}:{it['line']}`" if it.get("path") and it.get("line") else f"**{it['title']}**"
            in_body.append(f"{loc}\n\n{body.strip()}")
    review_body = "\n\n---\n\n".join(x for x in [summary, *in_body] if x)
    payload = {"commit_id": head, "body": review_body, "comments": inline}  # no "event": stays PENDING
    result = {"inline": len(inline), "inBody": len(in_body), "summary": bool(summary),
              "url": f"https://github.com/{owner}/{repo}/pull/{num}/files"}
    if dry_run:
        return {**result, "payload": payload}

    review = json.loads(gh(["api", "--method", "POST", f"repos/{owner}/{repo}/pulls/{num}/reviews", "--input", "-"],
                           json.dumps(payload)))
    return {**result, "record": record_post(work, review["id"], result["url"], [it["id"] for it, _ in items])}


def cmd_post(work: Path, dry_run: bool) -> int:
    try:
        res = post_review(work, dry_run)
    except (PostError, ConfigError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def cmd_serve(work: Path, port: int, open_browser: bool) -> int:
    index = work / "index.html"
    if not index.is_file():
        print(f"ERROR: {index} not found; run render first", file=sys.stderr)
        return 2
    # The token is injected into the served page; API calls must echo it, which a cross-origin
    # page cannot do without a preflight this server never answers.
    token = secrets.token_urlsafe(18)
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, code: int, body: bytes, ctype: str = "application/json") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def json(self, code: int, obj: dict) -> None:
            self.reply(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

        def authed(self) -> bool:
            if self.headers.get("X-Grok-Token") == token:
                return True
            self.json(403, {"error": "bad token"})
            return False

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                html = read_text(index).replace("<head>", f'<head>\n<meta name="grok-token" content="{token}">', 1)
                return self.reply(200, html.encode("utf-8"), "text/html; charset=utf-8")
            if self.path == "/api/state" and self.authed():
                with lock:
                    return self.json(200, load_decisions(work))
            if self.path != "/api/state":
                self.reply(404, b"{}")

        def do_PUT(self):
            if self.path != "/api/decisions":
                return self.reply(404, b"{}")
            if not self.authed():
                return
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            with lock:
                state = load_decisions(work)
                state["decisions"] = body.get("decisions", {})
                save_decisions(work, state)
            self.json(200, {"ok": True})

        def do_POST(self):
            if self.path != "/api/post":
                return self.reply(404, b"{}")
            if not self.authed():
                return
            try:
                with lock:
                    self.json(200, post_review(work))
            except (PostError, ConfigError) as exc:
                self.json(400, {"error": str(exc)})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Serving {work} at {url} (Ctrl+C to stop)", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def cmd_config(repo: Path | None) -> int:
    try:
        print(json.dumps(load_config(repo), indent=2))
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
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
    p_r.add_argument("--repo", type=Path, help="git repo to read source excerpts from")
    p_r.add_argument("--ref", default="HEAD", help="commit for excerpts; use the PR head SHA")
    p_s = sub.add_parser("serve", help="serve the page and save triage decisions")
    p_s.add_argument("work", type=Path)
    p_s.add_argument("--port", type=int, default=0)
    p_s.add_argument("--no-open", action="store_true")
    p_p = sub.add_parser("post", help="create a pending GitHub review from accepted findings")
    p_p.add_argument("work", type=Path)
    p_p.add_argument("--dry-run", action="store_true")
    p_f = sub.add_parser("fixes", help="print accepted findings as a fix list")
    p_f.add_argument("work", type=Path)
    p_c = sub.add_parser("config", help="print the effective scrutiny settings")
    p_c.add_argument("--repo", type=Path)
    p_t = sub.add_parser("threads", help="print a PR's review threads and review bodies as JSON")
    p_t.add_argument("url", help="https://github.com/<owner>/<repo>/pull/<n>")
    p_t.add_argument("--all", action="store_true", help="include resolved threads")
    args = parser.parse_args()
    # Comment text carries →, · and non-ASCII names; a cp1252 Windows console would raise on print.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    if args.cmd == "hunks":
        return cmd_hunks(args.diff)
    if args.cmd == "serve":
        return cmd_serve(args.work, args.port, not args.no_open)
    if args.cmd == "post":
        return cmd_post(args.work, args.dry_run)
    if args.cmd == "fixes":
        return cmd_fixes(args.work)
    if args.cmd == "config":
        return cmd_config(args.repo)
    if args.cmd == "threads":
        return cmd_threads(args.url, args.all)
    return cmd_render(args.guide, args.diff, args.out, not args.no_open, args.repo, args.ref)


if __name__ == "__main__":
    sys.exit(main())
