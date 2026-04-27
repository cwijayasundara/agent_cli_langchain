---
name: editing-the-chain
description: Use when modifying the LCEL chain composition in agent/chain.py.
---

# Editing the Chain

LCEL composes `Runnable`s with the `|` operator. Common building blocks:

- `RunnableLambda(fn)` — wraps a Python function.
- `RunnableParallel({"a": ra, "b": rb})` — fan-out.
- `RunnablePassthrough.assign(...)` — annotate the payload.
- `chat_model | parser` — terminate with a parser.

Compose left-to-right; the result of one stage is the input to the next.
