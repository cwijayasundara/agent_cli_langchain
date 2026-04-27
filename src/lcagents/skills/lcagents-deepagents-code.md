---
name: lcagents-deepagents-code
description: Use when editing a DeepAgents project — adding tools, sub-agents, modifying the system prompt, or working with the virtual filesystem.
---

# DeepAgents Code Patterns

## Construction

    from deepagents import create_deep_agent
    agent = create_deep_agent(model=..., tools=TOOLS, subagents=SUBAGENTS, instructions=PROMPT)

`create_deep_agent` returns a compiled LangGraph — `.invoke`, `.stream`, `.astream` all work.

## Sub-agents

    SUBAGENTS = [
        {"name": "researcher", "description": "...", "prompt": "..."},
    ]

The DeepAgent automatically exposes a `task` tool that delegates to the sub-agent by name.

## Built-ins

DeepAgents already provides: `write_todos` (planning), `read_file` / `write_file` / `edit_file` / `ls` / `glob` / `grep` (virtual FS), `task` (sub-agent delegation), context auto-summarisation. Don't re-implement them.
