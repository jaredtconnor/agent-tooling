---
name: tdd
description: Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development.
version: 1.0.0
---

## Philosophy
**Core principle**: Tests should verify behaviour through public interfaces, not implementation details. Code can change entirely; tests shouldn't.
**Good tests** are integration-style: they exercise real code paths through public APIs. They describe *what* the system does, not *how* it does it. A good test reads like a specification - "user can check out with valid cart" tells you exactly what capability exists. These tests survive refactors because they don't care about internal structure.
**Bad tests** are coupled to implementation. They mock internal collaborators, test private methods, or verify through external means (like querying a database directly instead of using the interface). The warning sign: your test breaks when you refactor, but behaviour hasn't changed. If you rename an internal function and tests fail, those tests were testing implementation, not behaviour.
See [references/tests.md](references/tests.md) for examples and [references/mocking.md](references/mocking.md) for mocking guidelines.
## Anti-Pattern: Horizontal Slices
**DO NOT write all tests first, then all implementation.** This is "horizontal slicing" - treating RED as "write all tests" and GREEN as "write all code."
This produces **crap tests**:
- Tests written in bulk test *imagined* behaviour, not *actual* behaviour
- You end up testing the *shape* of things (data structures, function signatures) rather than user-facing behaviour
- Tests become insensitive to real changes - they pass when behaviour breaks, fail when behaviour is fine
- You outrun your headlights, committing to test structure before understanding the implementation
**Correct approach**: Vertical slices via tracer bullets. One test → one implementation → repeat. Each test responds to what you learned from the previous cycle. Because you just wrote the code, you know exactly what behaviour matters and how to verify it.
```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
  ...
```
## Workflow
### 1. Planning
Before writing any code:
- [ ] Confirm with user what interface changes are needed
- [ ] Confirm with user which behaviour's to test (prioritize)
- [ ] Identify opportunities for deep modules (small interface, deep implementation)
- [ ] Design interfaces for testability
- [ ] List the behaviour's to test (not implementation steps)
- [ ] Get user approval on the plan
Ask: "What should the public interface look like? Which behaviour's are most important to test?"
**You can't test everything.** Confirm with the user exactly which behaviour's matter most. Focus testing effort on critical paths and complex logic, not every possible edge case.
### 2. Tracer Bullet
Write ONE test that confirms ONE thing about the system:
```
RED:   Write test for first behavior → test fails
GREEN: Write minimal code to pass → test passes
```
This is your tracer bullet - proves the path works end-to-end.
### 3. Incremental Loop
For each remaining behavior:
```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```
Rules:
- One test at a time
- Only enough code to pass current test
- Don't anticipate future tests
- Keep tests focused on observable behaviour
### 4. Refactor
After all tests pass, look for refactor candidates:
- [ ] Extract duplication
- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Apply SOLID principles where natural
- [ ] Consider what new code reveals about existing code
- [ ] Run tests after each refactor step
**Never refactor while RED.** Get to GREEN first.
## Checklist Per Cycle
```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only
[ ] Test would survive internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```

## Additional Resources
- For test examples (good vs bad), see [references/tests.md](references/tests.md)
- For mocking guidelines, see [references/mocking.md](references/mocking.md)
- For refactoring patterns, see [references/refactoring.md](references/refactoring.md)
- For deep module design, see [references/deep-modules.md](references/deep-modules.md)
- For interface design principles, see [references/interface-design.md](references/interface-design.md)
