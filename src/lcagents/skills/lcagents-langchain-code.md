---
name: lcagents-langchain-code
description: Use when editing a LangChain LCEL chain project — composing Runnables, retrievers, embeddings, chat models, parsers.
---

# LangChain (LCEL) Code Patterns

LCEL composes `Runnable`s with `|`.

## Building blocks

- `RunnableLambda(fn)` — wrap a Python callable.
- `RunnableParallel({"a": ra, "b": rb})` — fan-out.
- `RunnablePassthrough.assign(...)` — annotate the payload.
- `chat_model | parser` — terminate.

## Retrieval pattern

    retriever = vectorstore.as_retriever()
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt | llm | parser
    )
