---
name: langchain-agents-langgraph-code
description: Use when building a custom-graph LangGraph agent — when `create_agent(...)` + middleware isn't enough and you need explicit StateGraph control (multi-graph workflows, custom routing, non-standard state schemas, parallel branches). For the common case, use `create_agent` first (see middleware skill).
---

# LangGraph Code Patterns

## When to use raw StateGraph vs create_agent

**Use `create_agent(...)` first.** It covers single-LLM-with-tools agents, including ReAct-style loops, with full middleware support (retries, fallbacks, HITL, summarization). See the `langchain-agents-middleware` skill.

**Drop down to `StateGraph` when** you need:
- Multiple LLM calls in a single graph with custom routing between them.
- Branches that run in parallel and merge.
- Non-message state (custom dataclasses, dicts, dataframes flowing through nodes).
- Multi-graph workflows where one graph calls another as a subgraph.
- Direct control over node-level retries with `RetryPolicy`.

If your problem fits "one model, some tools, in a loop", you don't need this skill — read the middleware skill instead.

## Graph construction

```python
from langgraph.graph import StateGraph, START, END, MessagesState

g = StateGraph(MessagesState)
g.add_node("model", call_model)
g.add_edge(START, "model")
g.add_edge("model", END)
agent = g.compile()
```

## Conditional routing

```python
def route(state) -> str:
    return "tools" if state["messages"][-1].tool_calls else END

g.add_conditional_edges("model", route, {"tools": "tools", END: END})
```

## Tool nodes

```python
from langgraph.prebuilt import ToolNode
g.add_node("tools", ToolNode(TOOLS))
```

## Custom state schemas

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_action: str
    retry_count: int
```

The `Annotated[..., add_messages]` reducer appends rather than overwriting. Without a reducer, each node's return value replaces the field.

## Streaming

```python
for chunk in agent.stream({"messages": [...]}, stream_mode="updates"):
    ...
```

`stream_mode="values"` emits the full state after each node; `"updates"` emits only the diff per node; `"messages"` emits LLM tokens as they stream.

## Checkpointers (durable execution)

A graph becomes durable by attaching a checkpointer. Without one, `interrupt()` and HITL middleware can't function — the runtime has nowhere to save the suspended state.

```python
from langgraph.checkpoint.memory import InMemorySaver
agent = g.compile(checkpointer=InMemorySaver())  # dev only

# Production:
from langgraph.checkpoint.postgres import PostgresSaver
agent = g.compile(checkpointer=PostgresSaver.from_conn_string("postgresql://..."))
```

| Checkpointer | When |
|---|---|
| `InMemorySaver` | Dev / tests only — state dies with the process. |
| `SqliteSaver` | Single-node deploys, small scale. |
| `PostgresSaver` | Production. Survives restarts; supports concurrent threads. |

Each `agent.invoke(input, config)` requires a `thread_id` in `config`:

```python
result = agent.invoke(
    {"messages": [...]},
    config={"configurable": {"thread_id": "user-42-conv-7"}},
)
```

To resume a previously-interrupted thread, pass `None` as the input with the same `thread_id`:

```python
result = agent.invoke(None, config={"configurable": {"thread_id": "user-42-conv-7"}})
```

## Per-node retry policy

```python
from langgraph.pregel import RetryPolicy

g.add_node("flaky_api_call", call_external_api,
           retry_policy=RetryPolicy(max_attempts=5, initial_interval=1.0, backoff_factor=2.0))
```

This is for node-level retries on raw `StateGraph`. For `create_agent`-built agents, prefer `ToolRetryMiddleware` / `ModelRetryMiddleware` (see middleware skill).

## Subgraphs

```python
parent = StateGraph(ParentState)
parent.add_node("planning_subgraph", planning_graph.compile())
parent.add_node("execution_subgraph", execution_graph.compile())
```

Each subgraph runs to completion (or interrupt) before control returns to the parent.

## Common gotchas

- A node returning `{}` is a no-op; return `None` to signal "no state change" cleanly.
- `add_conditional_edges` mappings must include `END` if any branch terminates.
- `compile()` is not idempotent across `bind_tools` — rebind tools, then re-compile.
- `langgraph dev` reloads on file change; if it stops reloading, the graph likely failed to import — check the terminal for the exception.
- A graph with `interrupt()` calls but no checkpointer will throw at invoke time, not at compile time.
