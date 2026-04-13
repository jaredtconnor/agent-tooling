---
description: Analyse Claude Code sessions to identify improvements and learn from mistakes
---

# Session Analysis

Analyse Claude Code session transcripts to identify agent errors, user collaboration patterns, and hook effectiveness — then produce actionable recommendations for continuous improvement.

## Usage

```
/analyse
```

## What It Does

1. Asks whether to analyse the current session or recent sessions in this repository
2. Locates the relevant JSONL session logs
3. Invokes the session-analysis skill for structured analysis
4. Presents the report with prioritised recommendations
5. Optionally implements high-priority improvements (e.g., update CLAUDE.md, add a hook)

## Invoke Skill

```
Skill(session-analysis)
```

The skill handles the full analysis workflow: locate logs, extract patterns, assess against best practices, and generate recommendations.
