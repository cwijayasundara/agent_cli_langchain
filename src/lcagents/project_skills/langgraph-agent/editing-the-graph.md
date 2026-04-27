---
name: editing-the-graph
description: Use when adding nodes, edges, or conditional routing to the LangGraph agent.
---

# Editing the Graph

The graph lives in `agent/graph.py`. To add a node:

1. Define a function that takes `MessagesState` and returns `{"messages": [...]}`.
2. Call `g.add_node("name", fn)` inside `build_graph`.
3. Wire edges with `g.add_edge(...)` or `g.add_conditional_edges(...)`.

After editing, run `lcagents run "test prompt"` to confirm the graph still compiles.
