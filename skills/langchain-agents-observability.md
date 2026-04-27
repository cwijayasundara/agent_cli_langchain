---
name: langchain-agents-observability
description: Use when debugging an agent's behaviour, reading LangSmith traces, setting up tracing, or diagnosing common failure modes in LangChain / LangGraph / DeepAgents projects.
---

# Observability

LangChain ecosystem projects trace through **LangSmith**. Tracing is on whenever `LANGSMITH_TRACING=true` is set — no code changes required. Every `agent.invoke(...)` becomes one trace; tool calls and sub-agent delegations are nested spans.

## Required environment variables

```
LANGSMITH_API_KEY=ls_...        # required
LANGSMITH_TRACING=true          # enables capture
LANGSMITH_PROJECT=my-agent      # bucket name in the LangSmith UI
```

If `LANGSMITH_TRACING` is unset or `false`, the agent runs but no traces are captured. The agent does *not* fail — silent observability gap.

## Where traces live

LangSmith UI → the project named in `LANGSMITH_PROJECT`. Filter by experiment, time range, or status. Each trace is a tree: top-level `agent.invoke`, then nodes (LangGraph) or sub-agent `task` calls (DeepAgents) or chain steps (LCEL).

## Common failure-mode diagnostics

| Symptom | Likely cause | First thing to check |
|---|---|---|
| `agent` import fails | Missing dep, wrong path, syntax error | `python -c "from agent.agent import agent"` from project root |
| Smoke evals fail with auth error | Wrong / missing provider key | `python -c "import os; print(bool(os.getenv('OPENAI_API_KEY')))"` |
| Smoke evals fail with rate-limit | Provider rate limit during eval | Drop dataset to 1 row, then retry |
| `langgraph dev` hangs on start | `langgraph.json` graph path wrong | `cat langgraph.json` — verify `./agent/agent.py:agent` exists |
| `langgraph dev` reload stops working | Latest edit broke import | Check terminal for the exception; fix syntax error |
| Docker container crashes on boot | `.env` not passed at run time | `docker logs <container>` — look for missing-key errors |
| Cloud Run service doesn't start | Listening on 127.0.0.1 instead of 0.0.0.0:$PORT | `gcloud run services logs read SERVICE` |
| Trace shows the LLM but no tool calls | Tool not registered with the model | Verify `bind_tools(TOOLS)` (LangGraph) or that tools are in the `TOOLS` list passed to `create_deep_agent` |
| Trace shows tool calls but they fail | Tool raised an exception | Click the failing span — exception + traceback are captured |
| Conversation memory lost between turns | No checkpointer configured | LangGraph: pass `checkpointer=` to `compile()`. DeepAgents: same |
| Token cost suddenly spikes | Long context not being summarized | DeepAgents auto-summarizes; LangGraph does not — add manual summarization or trim |

## Quick local verification (no LangSmith needed)

```bash
python -c "
from agent.agent import agent
result = agent.invoke({'messages': [{'role': 'user', 'content': 'hello'}]})
print(result)
"
```

If this fails, the agent is broken regardless of tracing. Fix it first.

## Manual span instrumentation

If you need finer-grained spans inside a custom tool or node:

```python
from langsmith import traceable

@traceable
def my_helper(x: int) -> int:
    return x * 2
```

`@traceable` works on any callable; it shows up as its own span under the parent trace.

## Trace URLs

When `LANGSMITH_TRACING=true`, calling `agent.invoke(...)` from Python causes the SDK to print a trace URL to stderr. Capture it for debugging:

```python
result = agent.invoke({"messages": [...]})  # trace URL printed to stderr
```

For deploys, surface the LangSmith project URL to the user — they should be able to click through to see the live traffic.
