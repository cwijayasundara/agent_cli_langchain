---
name: langchain-agents-langchain-code
description: Use when editing a non-agentic LCEL pipeline — composing Runnables, retrievers, embeddings, chat models, parsers, or building a RAG chain. For agents (LLM + tools loop), use the middleware skill instead.
---

# LangChain (LCEL): editorial guidance

For API reference (full Runnable list, parser types, retriever interfaces), use the **`mcpdoc` MCP tools**: `fetch_docs("https://docs.langchain.com/oss/python/langchain/...")`. This skill is the *opinions* layer.

## When to use LCEL vs `create_agent`

LCEL is for **non-agentic flows**: deterministic pipelines (RAG, summarization, classification, structured extraction). The pipeline runs once, end-to-end, no loop, no tool-calling LLM driving control flow.

If the task involves an LLM deciding which tools to call, **don't use LCEL** — use `create_agent(...)` + middleware. Trying to bolt agentic behavior onto an LCEL chain is the most common mistake here. The dividing line: *does the LLM choose what happens next, or does the code?* If LLM, agents. If code, LCEL.

## Things the docs won't warn you about

- `chain.invoke(x)` where `x` is a string but the chain expects a dict will silently coerce in some configurations and fail in others — pass a dict explicitly.
- `init_chat_model` reads provider creds from env (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`). It will not prompt; missing env raises at first call, not at construction.
- Parsers are part of the chain. `chat_model.invoke(...)` returns an `AIMessage`; pipe through `StrOutputParser()` to get a plain string.
- **Middleware does NOT apply to LCEL chains.** Middleware is `create_agent`-only. For chains, use chain-level `chain.with_retry(...)` and `chain.with_fallbacks([...])` instead.
- `with_structured_output` does **not** stream — it accumulates the full response and returns the validated object. If you need streaming AND typed output, you can't have both via this API.

## Production rules of thumb

- **Always wrap production chains with `.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)`** for resilience to transient model failures.
- **For provider redundancy, use `.with_fallbacks([cheaper_model_chain])`** — fallback chains run if the primary raises. The fallback is a *full chain*, not just a model.
- **For typed output, use `model.with_structured_output(PydanticModel)`** before composing into the chain. Validation is automatic; you get the Pydantic instance, not a dict.
- **For RAG, add a guardrail stage** that returns "I don't know" when `len(context) == 0`. Without it, the LLM hallucinates from empty context.
- **For RAG, consider a reranker between retriever and prompt.** Recall@k improves substantially. The retriever's first 20 results passed through a reranker that picks the top 5 outperforms a retriever that fetches 5 directly.

## When to reach for what

| Need | Tool |
|---|---|
| LLM + tools, deciding what to do next | `create_agent` (NOT LCEL) |
| Deterministic transformation (text → structured) | LCEL with `with_structured_output` |
| RAG over a vector store | LCEL with `RunnableParallel` of retriever + question |
| Multi-step pipeline with branches | LCEL with `RunnableBranch` or upgrade to `StateGraph` if branches need state |
| Streaming token output | LCEL chain (most parsers stream); NOT `with_structured_output` |
| Async at scale | LCEL `.ainvoke` / `.astream` |

## Doc URLs to fetch with mcpdoc

- `https://docs.langchain.com/oss/python/langchain/lcel.md` — LCEL primer
- `https://docs.langchain.com/oss/python/langchain/structured-output.md` — `with_structured_output`
- `https://docs.langchain.com/oss/python/langchain/runnables.md` — Runnable types and methods
- `https://docs.langchain.com/oss/python/langchain/retrievers.md` — retriever interfaces
- `https://docs.langchain.com/oss/python/langchain/chat-models.md` — `init_chat_model` and provider model names

When you need a specific class signature or kwarg, fetch from these. Don't guess at constructor args.
