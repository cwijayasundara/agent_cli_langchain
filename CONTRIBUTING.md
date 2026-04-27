# Contributing

This repo is a pure skill bundle for coding agents working on LangChain / LangGraph / DeepAgents projects. Contributions are skill edits or new skills.

## How to propose a change

1. Fork.
2. Edit a skill in `skills/` (or add a new one — see *adding a skill* below).
3. Open a PR with a one-line summary of the change and what behavior the coding agent should now exhibit differently.

## What makes a good skill edit

- **One thing per skill.** A skill teaches a coding agent how to do *one* concern well (e.g. "deploying", "writing evals"). If your edit introduces a second concern, split it into a new skill.
- **Concrete recipes over prose.** Coding agents act on commands and code. Lead with the command or code block; explain afterward.
- **Cite official tools, not invented ones.** This bundle's value is teaching the agent to use `langgraph-cli` / `deepagents` / `langsmith` / `gcloud` / `docker` well. We don't invent abstractions.
- **Verify everything.** Every command in a skill must be one a maintainer can paste into a terminal and see work. Don't include speculative flags or invented APIs.
- **No silent footguns.** If a step has a non-obvious failure mode (rate-limit, missing API enable, secret not set), the skill must mention it.

## What makes a good new skill

A new skill is justified when:
- A coding agent today routinely makes the same mistake when working in this ecosystem, AND
- That mistake isn't covered (or covered well) by an existing skill, AND
- The fix is general enough to apply to most projects (not just one user's code).

If you're not sure, open a GitHub Discussion before writing the skill.

## Skill file format

Every skill file must:

1. Live under `skills/`.
2. Be named `langchain-agents-<concern>.md` (lowercase, hyphens).
3. Start with YAML frontmatter:

```markdown
---
name: langchain-agents-<concern>
description: Use when <specific trigger>. <One-line summary of what it teaches.>
---

# Title

(body — markdown)
```

The `description` is what coding agents read to decide whether to load the skill. Be specific. Vague descriptions (`"helps with langchain"`) make the skill never trigger or trigger constantly.

## Tested?

There are no automated tests. Skills are markdown documentation. Validate by:
1. Installing your edited bundle into your own `~/.claude/skills/` or `~/.codex/skills/`.
2. Asking your coding agent to do the relevant task in a real LangChain project.
3. Watching whether it follows the new guidance.

## License

By submitting a contribution you agree to license it under Apache-2.0.
