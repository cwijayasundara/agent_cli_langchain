---
name: langchain-agents-langchain-code
description: Use when editing a LangChain LCEL pipeline — composing Runnables, retrievers, embeddings, chat models, parsers, or building a RAG chain.
---

# LangChain (LCEL) Code Patterns

LCEL composes `Runnable`s with the `|` operator. Left-to-right; the result of one stage is the input to the next.

## Building blocks

- `RunnableLambda(fn)` — wrap a Python callable.
- `RunnableParallel({"a": ra, "b": rb})` — fan-out; output is a dict.
- `RunnablePassthrough()` — identity; emits its input.
- `RunnablePassthrough.assign(...)` — annotate the payload with extra fields.
- `chat_model | parser` — terminate with a parser (e.g. `StrOutputParser`).

## Standard chain shape

```python
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are concise."),
    ("human", "{question}"),
])
llm = init_chat_model("openai:gpt-4o-mini")
chain = prompt | llm | StrOutputParser()

result = chain.invoke({"question": "What is LCEL?"})
```

## RAG pattern

```python
from langchain_core.runnables import RunnablePassthrough

retriever = vectorstore.as_retriever()

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

The dict-with-Runnables shorthand is sugar for `RunnableParallel`. Each value runs in parallel against the input; the output is a dict that becomes the next stage's input.

## Streaming

```python
for token in chain.stream({"question": "..."}):
    print(token, end="", flush=True)
```

Most chat models support token streaming. Parsers like `StrOutputParser` pass tokens through.

## Async

```python
result = await chain.ainvoke({"question": "..."})
async for token in chain.astream({"question": "..."}):
    ...
```

## Common gotchas

- `chain.invoke(x)` where `x` is a string but the chain expects a dict will silently coerce in some configurations and fail in others — pass a dict explicitly.
- `init_chat_model` reads provider creds from env (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`). It will not prompt; missing env raises at first call.
- Parsers are part of the chain — `chat_model.invoke(...)` returns an `AIMessage`; pipe through `StrOutputParser()` to get a plain string.
