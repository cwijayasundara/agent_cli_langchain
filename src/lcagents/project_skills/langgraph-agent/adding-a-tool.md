---
name: adding-a-tool
description: Use when adding a new tool the agent can call.
---

# Adding a Tool

1. Open `agent/tools.py`.
2. Define the tool with `@tool` from `langchain_core.tools`.
3. Append it to the `TOOLS` list.
4. The graph picks it up automatically because `LLM.bind_tools(TOOLS)` is in `graph.py`.
5. Run `lcagents run "<prompt that should call the tool>"` to verify.
