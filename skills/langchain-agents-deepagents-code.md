---
name: langchain-agents-deepagents-code
description: Use when editing a DeepAgents project — adding tools, sub-agents, modifying the system prompt, or working with the virtual filesystem.
---

# DeepAgents Code Patterns

## Construction

```python
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model

agent = create_deep_agent(
    model=init_chat_model("anthropic:claude-sonnet-4-5"),
    tools=TOOLS,
    subagents=SUBAGENTS,
    instructions=PROMPT,
)
```

`create_deep_agent` returns a compiled LangGraph — `.invoke`, `.stream`, `.astream` all work, and the result is compatible with `langgraph dev` if you point a `langgraph.json` at it.

## Sub-agents

```python
SUBAGENTS = [
    {
        "name": "researcher",
        "description": "Searches the web and summarises findings.",
        "prompt": "You are a careful web researcher.",
    },
    {
        "name": "summariser",
        "description": "Compresses long text to bullets.",
        "prompt": "You produce terse bullet summaries.",
        "tools": [...],   # optional; sub-agent-only tools
    },
]
```

The DeepAgent automatically exposes a `task` tool that delegates to a sub-agent by name. The parent agent's tools are also available to sub-agents unless you scope them with the per-subagent `tools` key.

## Built-ins (do not re-implement)

DeepAgents already ships:
- `write_todos` — planning / task decomposition.
- `read_file` / `write_file` / `edit_file` / `ls` / `glob` / `grep` — virtual filesystem (in-memory unless you wire a real backend).
- `task` — sub-agent delegation.
- Context auto-summarization for long conversations.

Don't re-implement these. If you need a *real* filesystem instead of the virtual one, look at the `deepagents` filesystem backends (the package ships several, including a sandboxed shell).

## Custom tools

Same as LangChain — use `@tool`:

```python
from langchain_core.tools import tool

@tool
def fetch_user(user_id: str) -> dict:
    """Fetch a user record by id."""
    return {"id": user_id, "name": "..."}

TOOLS = [fetch_user]
```

Append to `TOOLS`; the agent picks them up automatically.

## Common gotchas

- The virtual filesystem persists across `agent.invoke(...)` calls within a single LangGraph run, but is reset between runs unless you pass a checkpointer.
- Sub-agent prompts are *templates* — the parent's `task` tool fills in `{description}`. Keep them generic.
- `instructions=` is the system prompt for the *top-level* DeepAgent, not for sub-agents. Each sub-agent has its own `prompt`.
