---
name: langchain-agents-langgraph-code
description: Use when building a custom-graph LangGraph agent — when `create_agent(...)` + middleware isn't enough and you need explicit StateGraph control (multi-graph workflows, custom routing, non-standard state schemas, parallel branches). For the common case, use `create_agent` first (see middleware skill).
---

# LangGraph: editorial guidance

For API reference (signatures, imports, exhaustive method lists), use the **`mcpdoc` MCP tools**: `fetch_docs("https://docs.langchain.com/oss/python/langgraph/...")`. This skill is the *opinions* layer; the docs are the *facts* layer.

## When to drop down to raw `StateGraph`

Most agents do NOT need this. Use `create_agent(...)` + middleware first (see the `langchain-agents-middleware` skill). Drop down to `StateGraph` only when:

- Multiple LLM calls in a single graph with custom routing between them.
- Branches that run in parallel and merge.
- Non-message state (custom dataclasses, dicts, dataframes flowing through nodes).
- Multi-graph workflows where one graph calls another as a subgraph.

If your problem fits "one model, some tools, in a loop" — even if the loop is complex — `create_agent` is the right tool. Don't reach for `StateGraph` out of habit.

## Things the docs won't warn you about

- A node returning `{}` is a no-op; return `None` to signal "no state change" cleanly.
- `add_conditional_edges` mappings must include `END` if any branch terminates — leaving it out is a silent bug, not an error.
- `compile()` is not idempotent across `bind_tools` — rebind tools, then re-compile.
- `langgraph dev` reloads on file change; if it stops reloading, the graph likely failed to import — check the terminal for the exception.
- A graph with `interrupt()` calls but no checkpointer will throw at *invoke time*, not at *compile time*. Always pair `interrupt()` with `compile(checkpointer=...)`.

## Production essentials (rules of thumb)

- **Always pass a `thread_id`** in `config={"configurable": {"thread_id": ...}}` for any agent with persistent state. A missing `thread_id` silently starts a fresh thread.
- **`InMemorySaver` is for dev only.** Production = `PostgresSaver` (multi-instance safe) or `SqliteSaver` (single-node, low-volume). State dies with the process for `InMemorySaver`.
- **Resume an interrupted thread by passing `None` as input** with the same `thread_id`. The runtime picks up where the interrupt fired.
- **Custom state schemas need reducers.** `Annotated[list, add_messages]` appends; without the reducer, each node *replaces* the field instead of accumulating.
- **For node-level retries on raw `StateGraph`, use `RetryPolicy`.** For `create_agent` agents, prefer `ToolRetryMiddleware` / `ModelRetryMiddleware` — same effect, cleaner composition.

## Doc URLs to fetch with mcpdoc

- `https://docs.langchain.com/oss/python/langgraph/graph-api.md` — `StateGraph`, nodes, edges
- `https://docs.langchain.com/oss/python/langgraph/durable-execution.md` — checkpointers + `thread_id`
- `https://docs.langchain.com/oss/python/langgraph/streaming.md` — `stream_mode` modes
- `https://docs.langchain.com/oss/python/langgraph/persistence.md` — Postgres / Sqlite checkpointers
- `https://docs.langchain.com/oss/python/langgraph/subgraphs.md` — multi-graph composition

When the user is mid-task and you need a method signature or import path, fetch from these URLs. Don't guess.
