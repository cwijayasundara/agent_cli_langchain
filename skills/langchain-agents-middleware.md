---
name: langchain-agents-middleware
description: Use when building or productionising any agent — adding retries, fallbacks, summarization, human-in-the-loop, PII redaction, call limits, or custom hooks. Middleware is THE composition primitive for modern LangChain agents (v1+); covers built-ins plus the custom middleware authoring API.
---

# Agentic Middleware

Middleware is how you compose cross-cutting agent behavior in LangChain v1+. It plugs into `create_agent(...)` (and is the underlying implementation of DeepAgents). **For any production agent, the question is "which middlewares" — not "do I need middleware".**

## The model

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    SummarizationMiddleware,
    ModelRetryMiddleware,
    ModelFallbackMiddleware,
    ModelCallLimitMiddleware,
    ToolRetryMiddleware,
    PIIMiddleware,
)

agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[...],
    middleware=[
        ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
        ModelFallbackMiddleware("openai:gpt-4o-mini"),
        ModelCallLimitMiddleware(run_limit=50),
        ToolRetryMiddleware(max_retries=3, backoff_factor=2.0),
        SummarizationMiddleware(model="claude-haiku-4-5", trigger=("tokens", 4000), keep=("messages", 20)),
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
    ],
)
```

`create_agent` returns a compiled LangGraph. All `Runnable` semantics apply: `.invoke`, `.ainvoke`, `.stream`, `.astream`, `langgraph dev`, `langgraph build`, etc.

## Lifecycle hooks (for custom middleware)

Every middleware can override one or more of these:

| Hook | Fires | Return |
|---|---|---|
| `before_agent(state, runtime)` | Once, before the loop starts | dict to merge into state, or None |
| `before_model(state, runtime)` | Before each model call | dict to merge into state, or None |
| `wrap_model_call(request, handler)` | Wraps the model call | call `handler(request)` → `ModelResponse`; return it (possibly modified) |
| `after_model(state, runtime)` | After each model response | dict to merge into state, or None |
| `wrap_tool_call(request, handler)` | Wraps each tool call | call `handler(request)` → `ToolMessage \| Command`; return it (possibly modified) |
| `after_agent(state, runtime)` | Once, after the loop ends | dict to merge into state, or None |

Node-style hooks (`before_*` / `after_*`) run sequentially. Wrap-style hooks compose like Python decorators — **first middleware in the list is the outermost wrapper**.

## Built-in middlewares (provider-agnostic)

Import from `langchain.agents.middleware`:

| Middleware | Purpose | Constructor |
|---|---|---|
| `SummarizationMiddleware` | Auto-summarize long conversations to stay under token limits | `(model, trigger=("tokens", N), keep=("messages", N))` |
| `HumanInTheLoopMiddleware` | Pause for human approve/edit/reject on sensitive tool calls | `(interrupt_on={"tool_name": {"allowed_decisions": [...]}})` — **requires a checkpointer** |
| `ModelCallLimitMiddleware` | Cap model calls per run / per thread (cost containment, infinite-loop guard) | `(thread_limit, run_limit, exit_behavior="end")` |
| `ToolCallLimitMiddleware` | Cap tool calls globally or per-tool | `(thread_limit, run_limit)` or `(tool_name, thread_limit, run_limit)` |
| `ModelRetryMiddleware` | Retry transient model failures with exponential backoff | `(max_retries, backoff_factor, initial_delay)` |
| `ToolRetryMiddleware` | Retry transient tool failures with exponential backoff | same args |
| `ModelFallbackMiddleware` | Fall back to alternative models on primary failure | `("model-1", "model-2", ...)` |
| `LLMToolSelectorMiddleware` | Use a small LLM to pick which tools to expose to the main model | `(model, max_tools, always_include=[...])` |
| `PIIMiddleware` | Detect & redact / mask / block PII | `("email"\|"credit_card"\|..., strategy="redact"\|"mask"\|"block", apply_to_input=True)` |
| `ContextEditingMiddleware` | Drop old tool outputs from context to free tokens | `(edits=[ClearToolUsesEdit(trigger, keep)])` |
| `TodoListMiddleware` | Adds the `write_todos` planning tool to the agent | `()` |
| `LLMToolEmulator` | Replace tool execution with LLM-generated outputs (testing) | `()` — never use in production |
| `ShellToolMiddleware` | Persistent shell session as a tool, with execution policy | `(workspace_root, execution_policy)` |
| `FilesystemFileSearchMiddleware` | Glob + Grep tools over a filesystem | `(root_path, use_ripgrep=True)` |

DeepAgents-specific (import from `deepagents.middleware`):

| Middleware | Purpose |
|---|---|
| `FilesystemMiddleware` | Virtual or backed filesystem for the agent (read/write/edit/ls/glob/grep) |
| `SubAgentMiddleware` | Adds the `task` tool with named sub-agents |

`create_deep_agent(...)` is a thin wrapper over `create_agent(...)` that pre-installs `FilesystemMiddleware` + `SubAgentMiddleware` + `TodoListMiddleware`. You can compose additional middlewares on top.

## Production middleware stack (start here)

For any production agent, this is the default stack to copy and tune:

```python
middleware=[
    # Cost containment (set BEFORE retries — limits the multiplier)
    ModelCallLimitMiddleware(run_limit=50),
    ToolCallLimitMiddleware(run_limit=200),

    # Resilience to transient failures
    ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
    ToolRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),

    # Provider-level resilience
    ModelFallbackMiddleware("openai:gpt-4o-mini"),

    # Long-conversation hygiene
    SummarizationMiddleware(model="claude-haiku-4-5", trigger=("tokens", 8000), keep=("messages", 20)),

    # Privacy (only if user input may contain PII)
    PIIMiddleware("email", strategy="redact", apply_to_input=True),
    PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
]
```

Add `HumanInTheLoopMiddleware` for any tool that touches money, sends external messages, or makes irreversible changes. **Requires a checkpointer** (`InMemorySaver` for dev, `PostgresSaver` for production — see the deploy skill).

## Custom middleware

Inherit from `AgentMiddleware`:

```python
from typing import Any, Callable
from langchain.agents.middleware import (
    AgentMiddleware, AgentState, ModelRequest, ModelResponse,
)
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command


class TokenBudgetMiddleware(AgentMiddleware):
    """Hard-cap total tokens across the run. Halts the agent when exceeded."""

    def __init__(self, budget: int) -> None:
        self.budget = budget

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        used = request.state.get("tokens_used", 0)
        if used >= self.budget:
            # short-circuit: return a synthetic "stop" response without calling the model
            return ModelResponse(
                messages=[{"role": "assistant", "content": "Token budget exceeded."}],
                command=Command(goto="__end__"),
            )
        response = handler(request)
        # ... extract token count from response.usage and add to state
        return response
```

If you need extra fields in state, declare them on a subclass of `AgentState` and set `state_schema = MyState` on the middleware class.

## Hard rules

- **Order matters.** Limits before retries (so retries don't burn through your budget). Privacy redaction before logging. Summarization should run *before* the model call, not after.
- **HumanInTheLoopMiddleware needs a checkpointer.** Without one, interrupts have nothing to resume from.
- **`LLMToolEmulator` is a testing-only middleware.** Never ship it.
- **Retries cost money.** A `max_retries=3` with `backoff_factor=2` means up to 4 calls per failure. Set `ModelCallLimitMiddleware` BEFORE retries to cap the worst-case cost.
- **Don't roll your own retry/fallback/limit.** The built-ins handle the edge cases (jitter, retryable error classification, streaming-aware wrapping). Custom middleware is for app-specific concerns.

## Skills to load alongside this one

- `langchain-agents-deploy` — productionisation: durable execution, checkpointers, deployment.
- `langchain-agents-observability` — tracing what middleware actually does at runtime.
- `langchain-agents-langgraph-code` — when to drop down to raw `StateGraph` (rare, but real cases exist).
