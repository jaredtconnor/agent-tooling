# Agent Personas

Specialist personas provide a role, perspective, and output format. They are the
**who** in this repo's workflow model.

| Layer | What It Is | Example | Role |
| --- | --- | --- | --- |
| Skill | Workflow with steps and exit criteria | `test-driven-development` | The how |
| Persona | Role with a perspective and report format | `code-reviewer` | The who |
| Command | User-facing entry point | `/review` | The when |

## Invocation Rules

1. Invoke a persona directly when you need one perspective on one artifact.
2. Use a command when the workflow is repeatable enough to name.
3. Use fan-out only when the investigations are independent and can be merged.
4. Personas do not invoke other personas. Composition belongs to the user or a command.
5. Personas may invoke skills when a workflow applies.

## Groups

- `core/`: general-purpose utility personas.
- `languages/`: language and ecosystem specialists.
- `specialists/`: domain experts for review, security, performance, docs, UI, and platform work.
- `orchestration/`: planning and coordination personas.

## Adding A Persona

1. Create `agents/<group>/<name>.md`.
2. Use YAML frontmatter with at least `name` and `description`.
3. Define scope, perspective, output format, and non-goals.
4. Add the persona to the relevant section in the main `README.md`.
5. If the persona enables a new orchestration pattern, document it in `references/orchestration-patterns.md`.
