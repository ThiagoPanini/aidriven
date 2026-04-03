Turn a repeated Claude Code workflow into a reusable repository-local skill.

## When to Create a Skill

Create a skill when you notice:
- A workflow repeated across multiple sessions (3+ repetitions is a strong signal)
- A multi-step checklist that encodes project-specific conventions
- A decision pattern with known tradeoffs worth capturing once
- A recurring setup, validation, or audit task

## Skill Anatomy

```markdown
One-sentence description of what this skill does and when to use it.

## When to Use
<trigger conditions>

## Checklist / Workflow
- [ ] Step 1
- [ ] Step 2
...

## Key Conventions
- Decision and rationale
- Default and why it was chosen

## References (optional)
- Link to supporting file or doc
```

## Rules for Good Skills

- **Scoped**: one responsibility, one clear workflow
- **Concise**: keep the skill file under 100 lines; move extended examples to `.claude/commands/refs/<name>.md`
- **Actionable**: prefer checklists over prose paragraphs
- **Honest**: capture the *why* behind conventions, not just the *what*
- **Evolving**: update based on real usage; a stale skill is worse than none

## Process

1. Identify the pattern from the current session or a described workflow
2. Choose a clear kebab-case name (noun or verb-noun)
3. Draft the skill at `.claude/commands/<name>.md`
4. Add a one-line entry to `.claude/SKILLS.md` (name, file link, trigger description)
5. If the skill has long examples or references, create `.claude/commands/refs/<name>.md`

## After Creating

Tell the user:
- The skill name and how to invoke it (`/<name>`)
- What it does in one sentence
- Any conventions or assumptions baked in that they should know about
