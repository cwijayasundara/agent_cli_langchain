---
name: adding-a-subagent
description: Use when adding a sub-agent the DeepAgent can delegate to.
---

# Adding a Sub-Agent

1. Open `agent/subagents.py`.
2. Append a dict to `SUBAGENTS` with keys: `name`, `description`, `prompt`. Optional: `tools`.
3. The DeepAgent will surface this sub-agent via its built-in `task` tool.

Example:

    SUBAGENTS = [
        {
            "name": "summariser",
            "description": "Compresses long text to bullet points.",
            "prompt": "You produce terse bullet summaries.",
        },
    ]
