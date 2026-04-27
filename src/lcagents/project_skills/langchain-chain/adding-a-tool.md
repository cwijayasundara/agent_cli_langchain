---
name: adding-a-tool
description: Use when adding a callable to compose into the LCEL chain.
---

# Adding a Tool (LCEL chains)

For LCEL chains, "tool" usually means: a function you wrap with `RunnableLambda` and pipe into the chain.

1. Open `agent/tools.py` and add the function.
2. Open `agent/chain.py` and import + compose it.
3. `lcagents run "<prompt>"` to verify.
