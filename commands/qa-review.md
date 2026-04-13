---
description: Assess repository QA readiness for agentic engineering workflows
---

# QA Readiness Review

Analyse a repository against the Tiered Test Gate framework (Tiers 0-5) and produce an assessment with actionable recommendations mapped to foundations best practices.

## Usage

```
/qa-review [path-to-repo]
```

If no path is provided, reviews the current working directory.

## What It Does

1. Scans repository structure and technology stack
2. Detects testing infrastructure, quality gates, CI/CD pipelines, and task runners
3. Scores each tier (0-5) on a 0-10 scale
4. Generates prioritised recommendations mapped to specific foundations skills
5. Optionally saves the report as `QA-READINESS-REVIEW.md`

## Invoke Skill

```
Skill(qa-review)
```

The skill handles the full workflow: scan, detect, score, recommend, and report.
