---
name: lcagents-scaffold
description: Use when creating a new lcagents project, when adding deploy/evals to an existing one, or when upgrading a project to a newer CLI version.
---

# lcagents Scaffolding

## Templates

- **`langgraph-agent`** — full StateGraph control. Pick when the user wants explicit nodes/edges/conditional routing.
- **`deep-agent`** — uses `create_deep_agent`. Pick for batteries-included planning agents with sub-agents and a virtual filesystem.
- **`langchain-chain`** — LCEL `Runnable` pipeline. Pick for non-agentic flows: RAG, summarisation, classification.

## Create

    lcagents scaffold create my-project --template langgraph-agent --deploy-target docker

The CLI refuses to overwrite an existing directory.

## Enhance an existing project

- `lcagents scaffold enhance --add docker` — drops in `server/` + Dockerfile if missing.
- `lcagents scaffold enhance --add evals` — drops in `evals/` scaffolding.
- `lcagents scaffold enhance --target {langsmith|docker}` — switches the default deploy target in `.agents/lcagents.toml`.

## Upgrade

`lcagents scaffold upgrade` re-syncs `CLAUDE.md`, `AGENTS.md`, `.agents/skills/`, and `server/Dockerfile` to the current CLI's template content using a 3-way merge against `.agents/baseline/`. Conflicts are written as `<file>.lcagents-upgrade.txt` next to the original; resolve them by hand and delete the conflict file.
