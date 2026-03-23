Analyze the git repository history to extract lessons, patterns, and preferences for compounding engineering. Use the lesson-extractor and pattern-propagator agents to build up our learning files from historical data.

## What to Analyze

1. **Recent Commits (last 100-200)**
   - Extract patterns from commit messages
   - Identify bug fixes and their solutions
   - Find performance improvements
   - Document architectural changes

2. **Pull Request History**
   - Extract code review preferences
   - Identify approved vs rejected patterns
   - Document team conventions

3. **Error Fixes**
   - Find commits with "fix:", "bug:", "error:" prefixes
   - Extract root causes and solutions
   - Create prevention rules

4. **Feature Implementations**
   - Find commits with "feat:", "feature:", "add:" prefixes
   - Extract successful patterns
   - Document architectural decisions

5. **Refactoring Patterns**
   - Find commits with "refactor:", "improve:", "optimize:" prefixes
   - Extract improvement patterns
   - Document performance gains

## Agents to Use

1. **lesson-extractor**:
   - Process commit history to extract lessons
   - Update CLAUDE-lessons.md with discoveries
   - Create error prevention rules in CLAUDE-troubleshooting.md
   - Document preferences in CLAUDE-preferences.md

2. **pattern-propagator**:
   - Identify successful patterns from commits
   - Find where patterns can be applied
   - Update CLAUDE-patterns.md with reusable patterns
   - Track pattern adoption opportunities

## Output Files to Create/Update

- **CLAUDE-lessons.md**: Historical lessons with impact metrics
- **CLAUDE-patterns.md**: Successful patterns to propagate
- **CLAUDE-troubleshooting.md**: Error fixes and prevention
- **CLAUDE-preferences.md**: Team coding preferences
- **CLAUDE-agent-knowledge.md**: Cross-agent learnings

## Process

1. Analyze git log for patterns and lessons
2. Extract measurable improvements from commit messages
3. Identify recurring patterns across commits
4. Document with proper IDs ([TYPE-YYYY-MM-DD-NNN])
5. Include "receipts" (commit hashes, PR numbers)
6. Calculate compound impact where possible
7. Create cross-references between related lessons

## Success Metrics

Track and report:
- Total lessons extracted
- Patterns identified
- Estimated time savings
- Error categories prevented
- Velocity improvements projected

Remember: Every commit teaches something. Every fix prevents recurrence. Every pattern compounds value.
