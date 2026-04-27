---
name: langchain-agents-langgraph-code
description: Use when editing a LangGraph project — adding nodes, edges, conditional routing, checkpointers, streaming, or state schemas.
---

# LangGraph Code Patterns

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

## Checkpointers (persistence)

```python
from langgraph.checkpoint.memory import MemorySaver
agent = g.compile(checkpointer=MemorySaver())
```

For production, swap `MemorySaver` for `PostgresSaver` or `SqliteSaver`.

## Streaming

```python
for chunk in agent.stream({"messages": [...]}, stream_mode="updates"):
    ...
```

`stream_mode="values"` emits the full state after each node; `"updates"` emits only the diff.

## State schemas beyond `MessagesState`

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_action: str
    retry_count: int
```

The `Annotated[..., add_messages]` reducer appends rather than overwriting.

## Common gotchas

- A node returning `{}` is a no-op; return `None` to signal "no state change" cleanly.
- `add_conditional_edges` mappings must include `END` if any branch terminates.
- `compile()` is not idempotent across `bind_tools` — rebind tools, then re-compile.
- `langgraph dev` reloads on file change; if it stops reloading, the graph likely failed to import — check the terminal for the exception.
