---
name: lcagents-workflow
description: Use when scaffolding a LangChain agent project, or when working in any project with .agents/lcagents.toml. Teaches the develop -> evals -> deploy lifecycle and which command to reach for at each step.
---

# lcagents Workflow

`lcagents` is a Python CLI for scaffolding, running, evaluating, and deploying LangChain / LangGraph / DeepAgents projects. **It is a tool for you (the coding agent), not a coding agent itself.** Don't try to use it to chat or reason; use it to take actions.

## When to invoke which command

| Goal | Command |
|---|---|
| Start a new project | `lcagents scaffold create <name> --template {langgraph-agent\|deep-agent\|langchain-chain}` |
| Install deps | `lcagents install` |
| Set provider/LangSmith keys | `lcagents login` |
| Smoke-test the agent | `lcagents run "<prompt>"` |
| Interactive dev | `lcagents dev` |
| Run evals | `lcagents eval run` (or `--smoke` for the 3-row dataset) |
| Compare evals | `lcagents eval compare a.json b.json` |
| Deploy | `lcagents deploy {langsmith\|docker}` |
| Add docker/evals to existing project | `lcagents scaffold enhance --add {docker\|evals}` |
| Re-sync after a CLI bump | `lcagents scaffold upgrade` |

## Hard rules

- The runnable agent is **always** exported as `agent` from `agent/agent.py`. Never rename it.
- Read the project-local skills under `.agents/skills/` before editing — they describe the specific shape of *this* project.
- Both `deploy` commands run a smoke pre-flight. If they refuse, fix the agent or the smoke dataset; do not bypass.
- `LANGSMITH_API_KEY` is required for evals and the LangSmith deploy path.
