---
name: langchain-agents-deepagents-code
description: Use when editing a DeepAgents project — adding tools, sub-agents, modifying the system prompt, choosing a filesystem backend, or composing extra middlewares (retries, fallbacks, HITL) on top.
---

# DeepAgents Code Patterns

DeepAgents is `create_agent(...)` pre-loaded with three middlewares: `FilesystemMiddleware` (virtual FS + read/write/edit/ls/glob/grep tools), `SubAgentMiddleware` (the `task` tool with named sub-agents), and `TodoListMiddleware` (the `write_todos` planning tool). You can stack additional middlewares on top.

## Construction

```python
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model

agent = create_deep_agent(
    model=init_chat_model("anthropic:claude-sonnet-4-6"),
    tools=TOOLS,
    subagents=SUBAGENTS,
    instructions=PROMPT,
)
```

`create_deep_agent` returns a compiled LangGraph — `.invoke`, `.stream`, `.astream` all work. Compatible with `langgraph dev`, `langgraph build`, LangSmith, and a `langgraph.json` pointing at `agent.agent:agent`.

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

- `write_todos` — planning / task decomposition.
- `read_file` / `write_file` / `edit_file` / `ls` / `glob` / `grep` — filesystem tools (virtual unless you wire a real backend).
- `task` — sub-agent delegation.
- Context auto-summarization for long conversations.

## Filesystem backend (choose one for production)

The default `FilesystemMiddleware` uses an **in-memory virtual FS**, reset between invocations unless you pass a checkpointer. For production:

```python
from deepagents import create_deep_agent
from deepagents.middleware.filesystem import FilesystemMiddleware
# from deepagents.backends import StoreBackend, CompositeBackend

agent = create_deep_agent(
    model=...,
    middleware=[
        # Override the default FilesystemMiddleware with a backed one
        FilesystemMiddleware(backend=...),
    ],
)
```

Backend choices (per LangChain docs):

| Backend | Scope | When |
|---|---|---|
| Default (in-memory) | Single invocation | Dev, tests |
| `StateBackend` | Single thread (with checkpointer) | Conversation memory |
| `StoreBackend(namespace=(assistant_id, user_id))` | Per-user persistent | Production: each user gets private files |
| `CompositeBackend` | Mix scopes | E.g. ephemeral scratch + persistent `/memories/` |

User-scoped (`StoreBackend`) is the recommended default for production — each user's files are isolated.

## Sandboxed shell execution

For tools that need to run real shell commands, use `ShellToolMiddleware` with a sandboxed execution policy (Daytona is the primary supported sandbox per the docs). Two lifecycle patterns: thread-scoped (fresh container per conversation; cleaned up on TTL) and assistant-scoped (shared across conversations).

**Critical:** never pass raw API keys into a sandbox. Agents can read any file the sandbox can. Use the auth proxy to inject credentials at call time.

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

## Production middleware composition

Stack the production middleware stack on top of the built-ins:

```python
from deepagents import create_deep_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware, ToolCallLimitMiddleware,
    ModelRetryMiddleware, ToolRetryMiddleware,
    ModelFallbackMiddleware, SummarizationMiddleware,
    HumanInTheLoopMiddleware, PIIMiddleware,
)

agent = create_deep_agent(
    model="claude-sonnet-4-6",
    tools=TOOLS,
    subagents=SUBAGENTS,
    instructions=PROMPT,
    middleware=[
        ModelCallLimitMiddleware(run_limit=50),
        ToolCallLimitMiddleware(run_limit=200),
        ModelRetryMiddleware(max_retries=3),
        ToolRetryMiddleware(max_retries=3),
        ModelFallbackMiddleware("openai:gpt-4o-mini"),
        SummarizationMiddleware(model="claude-haiku-4-5", trigger=("tokens", 8000), keep=("messages", 20)),
        HumanInTheLoopMiddleware(interrupt_on={"send_email": {"allowed_decisions": ["approve","edit","reject"]}}),
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
    ],
)
```

See the `langchain-agents-middleware` skill for the full middleware reference.

## Common gotchas

- The virtual FS persists across `agent.invoke(...)` calls within a single LangGraph run, but resets between runs unless you pass a checkpointer with a stable `thread_id`.
- Sub-agent prompts are *templates* — the parent's `task` tool fills in `{description}`. Keep them generic.
- `instructions=` is the system prompt for the *top-level* DeepAgent, not for sub-agents. Each sub-agent has its own `prompt`.
- Adding `HumanInTheLoopMiddleware` requires a checkpointer at compile time — `create_deep_agent` accepts a `checkpointer=` parameter for this.
