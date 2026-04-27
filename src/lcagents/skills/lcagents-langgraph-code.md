---
name: lcagents-langgraph-code
description: Use when editing a LangGraph project — adding nodes, edges, conditional routing, checkpointers, streaming, or state schemas.
---

# LangGraph Code Patterns

## Graph construction

    from langgraph.graph import StateGraph, START, END, MessagesState

    g = StateGraph(MessagesState)
    g.add_node("model", call_model)
    g.add_edge(START, "model")
    g.add_edge("model", END)
    agent = g.compile()

## Conditional routing

    def route(state) -> str:
        return "tools" if state["messages"][-1].tool_calls else END

    g.add_conditional_edges("model", route, {"tools": "tools", END: END})

## Tool nodes

    from langgraph.prebuilt import ToolNode
    g.add_node("tools", ToolNode(TOOLS))

## Checkpointers (persistence)

    from langgraph.checkpoint.memory import MemorySaver
    agent = g.compile(checkpointer=MemorySaver())

## Streaming

    for chunk in agent.stream({"messages": [...]}, stream_mode="updates"):
        ...
