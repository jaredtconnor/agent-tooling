---
description: Assess CI/CD pipeline quality and generate improvement recommendations
---

# CI/CD Pipeline Review

Analyse a repository's CI/CD pipelines against the 5-pillar framework (Build, Integration & E2E Tests, Static Analysis, Security, Agentic PR Review) and produce a scored assessment with actionable recommendations.

## Usage

```
/cicd-review [path-to-repo]
```

If no path is provided, reviews the current working directory.

## What It Does

1. Detects CI platform and reads all workflow files
2. Pulls live data via `gh` CLI (run history, cache usage, branch protection, alerts)
3. Scores each pillar (1-5) on a 0-10 scale
4. Generates prioritised recommendations mapped to `Task(platform-engineer)` and foundations skills
5. Optionally saves the report as `CICD-PIPELINE-REVIEW.md`

## Invoke Skill

```
Skill(cicd-review)
```

The skill handles the full workflow: detect, read, review live data, score, recommend, and report.
