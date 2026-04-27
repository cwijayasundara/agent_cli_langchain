---
name: lcagents-observability
description: Use when debugging an agent's behaviour, reading LangSmith traces, or setting up tracing in a fresh project.
---

# lcagents Observability

LangSmith tracing is on whenever `LANGSMITH_TRACING=true` is in `.env` (it's set by default in scaffolded projects).

## Where traces live

LangSmith UI -> `LANGSMITH_PROJECT` (defaults to the project name). Each `agent.invoke(...)` is one trace; tool calls and sub-agent delegations are nested spans.

## Common failure patterns

| Symptom | Likely cause |
|---|---|
| `agent` import fails | `agent/agent.py` doesn't export a symbol named `agent`, or imports broke |
| Smoke pre-flight fails | Provider key missing, model name typo, tool error |
| `langgraph dev` hangs | `langgraph.json` graph path wrong |
| Docker container crashes on boot | `.env` not passed at runtime |
