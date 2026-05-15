# Updating Existing CLAUDE Documentation

When CLAUDE documentation already exists, use this workflow to improve it.

## Update Workflow

1. **Analyze current state** - What documentation exists and when was it created?
2. **Identify changes** - What's changed in the codebase since documentation was created?
3. **Assess signal-to-noise** - Is current documentation helping or hindering agents?
4. **Propose changes** - Suggest updates, additions, and removals
5. **Execute updates** - Make approved changes
6. **Verify improvements** - Ensure documentation is more useful

## 1. Analyze Current Documentation State

```bash
# Find all documentation
find . -name "CLAUDE*.md" | sort

# Check when last modified
find . -name "CLAUDE*.md" -exec ls -l {} \;

# Get creation dates from git
find . -name "CLAUDE*.md" -exec git log --follow --format="%ai" --diff-filter=A {} \; | head -1
```

**Ask user about documentation quality:**

"I found [N] CLAUDE documentation files last updated [X days/months] ago.

How would you rate the current documentation?

1. Mostly accurate, minor updates needed
2. Some sections outdated, needs refresh
3. Significantly outdated, major overhaul needed"

## 2. Identify Changes Since Documentation Created

```bash
# Find when documentation was last updated
LAST_UPDATE=$(git log -1 --format="%ai" CLAUDE.md)

# Get commit summary since last doc update
git log --since="$LAST_UPDATE" --oneline --stat | head -100

# Look for new/deleted/renamed files
git diff --name-status HEAD $(git log -1 --format="%H" CLAUDE.md) | grep -E "^(A|D|R)"
```

**Key changes to identify:**

- New modules/directories - Need new CLAUDE.md files?
- Deleted modules - Remove corresponding CLAUDE.md files?
- Renamed modules - Update references?
- New dependencies - Update tech stack sections?
- New tooling - Update justfile commands?
- Removed tooling - Remove outdated commands?
- Architecture changes - Update architecture docs?

## 3. Assess Signal-to-Noise Ratio

**For each existing CLAUDE file, evaluate:**

1. **Relevance**: Does this information help agents complete tasks today?
   - YES → Keep
   - NO → Remove or move to separate doc

2. **Accuracy**: Is this information still correct?
   - YES → Keep
   - NO → Update or remove

3. **Specificity**: Is this specific to this codebase or generic advice?
   - SPECIFIC → Keep
   - GENERIC → Remove (agents can Google generic advice)

4. **Redundancy**: Is this duplicated elsewhere?
   - NO → Keep
   - YES → Keep in one place, remove from others

**Common signal-to-noise issues:**

- **Too long**: CLAUDE.md over 100 lines → Extract to separate files
- **Too detailed**: Implementation details → Move to code comments
- **Out of date**: Commands that don't exist → Remove or update
- **Generic**: "Always write tests" → Remove (obvious)
- **Speculative**: "We plan to..." → Remove (document what exists)

## 4. Propose Changes

Create a comprehensive update proposal for user approval before proceeding.

## 5. Execute Updates

**Update strategy for each file:**

1. Read current content
2. Identify what to keep (high signal)
3. Identify what to change (outdated or low signal)
4. Identify what to add (new information)
5. Rewrite file - keep minimal and focused
6. Verify accuracy against actual codebase

**Signal-to-noise filter:**

- Does this help agents complete tasks? → Keep
- Is this obvious or generic? → Remove
- Is this speculative? → Remove
- Is this outdated? → Update or remove

## 6. Verify Improvements

```bash
# Compare file sizes before/after
find . -name "CLAUDE*.md" -exec wc -l {} \;

# Verify no broken links
grep -r "See CLAUDE" . --include="CLAUDE*.md"

# Check for speculation keywords
grep -r "plan to\|will add\|future\|TODO" . --include="CLAUDE*.md"
```

**Quality checklist:**

- [ ] All CLAUDE.md files under size limits
- [ ] No broken references between files
- [ ] No speculation or future plans
- [ ] Only commands that actually exist
- [ ] High signal-to-noise ratio
- [ ] Information is current and accurate
