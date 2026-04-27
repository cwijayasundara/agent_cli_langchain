---
name: langchain-agents-deepagents-code
description: Use when editing a DeepAgents project — adding tools, sub-agents, modifying the system prompt, choosing a filesystem backend, or composing extra middlewares (retries, fallbacks, HITL) on top.
---

# DeepAgents: editorial guidance

For API reference (signatures, kwargs, full middleware list), use the **`mcpdoc` MCP tools**: `fetch_docs("https://docs.langchain.com/oss/python/deepagents/...")`. This skill is the *opinions* layer.

## What DeepAgents actually is

`create_deep_agent(...)` is a thin wrapper over `create_agent(...)` that pre-installs three middlewares: `FilesystemMiddleware` (virtual FS + `read_file`/`write_file`/`edit_file`/`ls`/`glob`/`grep`), `SubAgentMiddleware` (the `task` tool with named sub-agents), and `TodoListMiddleware` (the `write_todos` planning tool). You can stack additional middlewares on top.

The implication: **everything you know about agentic middleware applies.** See `langchain-agents-middleware` for the production stack — DeepAgents projects benefit from it just like plain `create_agent` projects do.

## Filesystem backend — pick deliberately for production

The default `FilesystemMiddleware` uses an **in-memory virtual FS** that resets between invocations unless you pass a checkpointer. For production, choose a backend:

| Backend | Scope | When |
|---|---|---|
| Default (in-memory) | Single invocation | Dev, tests |
| `StateBackend` | Single thread (with checkpointer) | Conversation memory only |
| `StoreBackend(namespace=(assistant_id, user_id))` | Per-user persistent | Production: each user gets isolated files |
| `CompositeBackend` | Mix scopes | E.g. ephemeral scratch + persistent `/memories/` |

**`StoreBackend` namespaced by user is the production default.** Don't ship a multi-user agent with the in-memory default — files would leak across users.

## Sandboxed shell execution — read this before adding tool execution

For tools that run real shell commands, use `ShellToolMiddleware` with a sandboxed execution policy (Daytona is the primary supported sandbox). Two lifecycle patterns:
- **Thread-scoped** (most common): fresh container per conversation, cleaned up on TTL.
- **Assistant-scoped**: shared across conversations, preserves installed packages / cloned repos.

**Critical rule the docs only mention in passing:** never pass raw API keys into a sandbox. The agent can `read_file` any file the sandbox can. Use the auth proxy to inject credentials at call time. Treat sandboxes as adversarial environments.

## Sub-agent design rules of thumb

- **Sub-agent prompts are templates** — the parent's `task` tool fills in `{description}`. Keep prompts generic; the parent decides the specifics.
- **`instructions=` is for the top-level agent**, not for sub-agents. Each sub-agent has its own `prompt` field.
- **Scope tools per sub-agent.** A `researcher` sub-agent rarely needs `send_email`. The per-subagent `tools` key narrows the surface and improves reliability.
- **Don't nest sub-agents more than one level deep.** Two-level nesting works; three-level becomes hard to reason about and hard to trace.

## When to compose extra middlewares (almost always)

`create_deep_agent` accepts a `middleware=[...]` parameter that adds to (not replaces) the built-in three. For any production DeepAgent, layer the production stack on top:

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
        # HITL on irreversible tools — requires checkpointer
        HumanInTheLoopMiddleware(interrupt_on={"send_email": {"allowed_decisions": ["approve","edit","reject"]}}),
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
    ],
)
```

## Things the docs won't warn you about

- The virtual FS persists across `agent.invoke(...)` calls within a single LangGraph run, but resets between runs unless you pass a checkpointer with a stable `thread_id`.
- Adding `HumanInTheLoopMiddleware` requires a checkpointer at compile time. `create_deep_agent` accepts a `checkpointer=` parameter for this.
- Sub-agents share the parent's tool registry by default. If a sub-agent should NOT see a tool, scope explicitly.

## Doc URLs to fetch with mcpdoc

- `https://docs.langchain.com/oss/python/deepagents/index.md` — overview
- `https://docs.langchain.com/oss/python/deepagents/going-to-production.md` — backends, sandboxes, deployment
- `https://docs.langchain.com/oss/python/deepagents/memory.md` — filesystem backends in depth
- `https://docs.langchain.com/oss/python/deepagents/human-in-the-loop.md` — HITL patterns
