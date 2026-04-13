---
description: Add or confirm a label on a Linear issue (bug/chore/feature)
---

# Label - Classify Linear Issues

Add or confirm a type label (bug/chore/feature) on a Linear issue.

## Usage

```bash
/label AIFE-123 bug       # Label as bug
/label AIFE-123 chore     # Label as chore
/label AIFE-123 feature   # Label as feature
/label AIFE-123           # Interactive - show suggestion and confirm
```

## Overview

Used to classify issues that are missing a type label. The conductor shows unlabeled issues with suggested labels - this command confirms or overrides the suggestion.

## Process

### With Label Argument

```python
def label_issue(issue_id: str, label: str):
    """Apply label to issue."""
    if label not in ['bug', 'chore', 'feature']:
        print(f"Invalid label: {label}")
        print("Valid labels: bug, chore, feature")
        return

    # Get issue
    issue = mcp__linear_server__get_issue(id=issue_id)

    # Add label
    mcp__linear_server__update_issue(
        id=issue['id'],
        labels=[label]
    )

    print(f"Labeled {issue_id} as {label}")

    # Issue will be re-classified on next conductor poll
```

### Interactive (No Label Argument)

```python
def label_issue_interactive(issue_id: str):
    """Interactive label selection with suggestion."""
    issue = mcp__linear_server__get_issue(id=issue_id)

    # Suggest label based on content
    suggested = suggest_label(issue)

    print(f"Issue: {issue['identifier']} - {issue['title']}")
    print(f"Suggested label: {suggested}")
    print()
    print("Select label:")
    print(f"  1. {suggested} (suggested)")
    print("  2. bug")
    print("  3. chore")
    print("  4. feature")

    # User selects option
    # Apply selected label
```

## Examples

```bash
# Conductor shows:
# 🏷️  UNLABELED (Need Classification)
# └─ AIFE-210 "Improve search" [suggest: feature] → /label AIFE-210

# Confirm suggestion:
/label AIFE-210 feature
# Output: Labeled AIFE-210 as feature

# Override suggestion:
/label AIFE-210 chore
# Output: Labeled AIFE-210 as chore

# Interactive:
/label AIFE-210
# Output:
# Issue: AIFE-210 - Improve search functionality
# Suggested label: feature
#
# Select label:
#   1. feature (suggested)
#   2. bug
#   3. chore
#   4. feature
```

## Integration

After labeling, the issue will be re-classified on the next conductor poll:

- **bug** (standalone) → Auto-kick `/bug-fix`
- **chore** (standalone) → Auto-kick `/chore`
- **feature** → Enter HITL workflow (needs_refine → needs_plan → etc.)

## Remember

- Valid labels: `bug`, `chore`, `feature`
- Conductor suggests labels based on title/description heuristics
- Re-classification happens on next poll
