---
name: langchain-agents-langchain-code
description: Use when editing a non-agentic LCEL pipeline — composing Runnables, retrievers, embeddings, chat models, parsers, or building a RAG chain. For agents (LLM + tools loop), use the middleware skill instead.
---

# LangChain (LCEL) Code Patterns

LCEL composes `Runnable`s with the `|` operator. Left-to-right; the result of one stage is the input to the next.

**Note:** Middleware (retries, fallbacks, HITL) is for `create_agent(...)` **only**. Chains compose it differently — fallbacks via `chain.with_fallbacks([...])`, retries via `chain.with_retry(...)`, structured output via `with_structured_output(schema)`. See below.

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

## Structured output

When you need typed/validated output (the common case for non-chat use):

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="Full name")
    age: int = Field(description="Age in years")

structured_llm = init_chat_model("openai:gpt-4o-mini").with_structured_output(Person)
result = structured_llm.invoke("Extract: Alice is 30.")
# result is a Person instance, validated.
```

`with_structured_output` accepts a Pydantic model, a TypedDict, or a JSON schema dict. The model decides whether to use native structured outputs (OpenAI/Anthropic) or function-calling under the hood — you don't have to.

## Retries and fallbacks (chain-level)

```python
# Retry transient failures
chain = (prompt | llm | parser).with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True,
)

# Fallback to a different chain on failure
fallback_chain = prompt | init_chat_model("anthropic:claude-haiku-4-5") | parser
chain = (prompt | llm | parser).with_fallbacks([fallback_chain])
```

These are chain-level analogues of middleware retries/fallbacks. They are **not** the same as the middleware versions and don't apply to `create_agent`-built agents.

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

For production RAG, also add:
- `with_retry()` for transient retriever failures.
- A reranker stage between retriever and prompt for better recall@k.
- A guardrail (e.g. `RunnableLambda` that returns a "I don't know" if `len(context) == 0`).

## Streaming

```python
for token in chain.stream({"question": "..."}):
    print(token, end="", flush=True)
```

Most chat models support token streaming. Parsers like `StrOutputParser` pass tokens through. `with_structured_output` does **not** stream — it accumulates the full response and returns the validated object.

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
- Trying to add agentic middleware to a chain will fail — middleware is for `create_agent` only. Use chain-level `.with_retry()` / `.with_fallbacks()` instead.
