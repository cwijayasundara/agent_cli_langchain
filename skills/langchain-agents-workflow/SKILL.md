---
name: langchain-agents-workflow
description: Use when starting work on any LangChain / LangGraph / DeepAgents project. Entry point for the develop -> middleware -> evaluate -> deploy lifecycle, mapping each step to the right official tool.
---

# LangChain Agents Workflow

This skill is the entry point — read it first, then load the more specific skill for the step you're on.

## You have two complementary tools

This skill bundle pairs with the **`mcpdoc` MCP server**. The two have distinct roles; use both.

| | `mcpdoc` (MCP server) | This skill bundle |
|---|---|---|
| Purpose | Live API reference | Opinionated playbook |
| Content | Whatever's on `docs.langchain.com` right now | How to *think* about LangChain projects |
| When to use | "What's the signature of `SummarizationMiddleware`?" / "What kwargs does `create_agent` take?" / "What import path for X?" | "What's the production middleware stack?" / "How do I wire Cloud Run + Secret Manager + Postgres checkpointer together?" / "Which mistakes does an agent typically make here?" |
| How to use | Call `fetch_docs(url)` or `list_doc_sources()` | Load skills based on description triggers |
| Drift risk | Zero — always live | Owner updates as ecosystem evolves; some rot tolerated |

**Rule of thumb:** when you need an exact API detail, fetch from `mcpdoc`. When you need to make a design decision, load a skill. When in doubt, do both.

## When to load which skill

| Goal | Skill |
|---|---|
| Start a new agent project | `langchain-agents-scaffold` |
| Build a modern agent (most cases) | `langchain-agents-middleware` ← first; uses `create_agent(...)` with middleware |
| Add nodes/edges/tools to a custom LangGraph | `langchain-agents-langgraph-code` |
| Customize a DeepAgent | `langchain-agents-deepagents-code` |
| Build a non-agentic LCEL pipeline (chains, RAG) | `langchain-agents-langchain-code` |
| Write or run evals; unit/integration test agents | `langchain-agents-langsmith-evals` |
| Deploy + productionise | `langchain-agents-deploy` |
| Debug / read traces / OTEL | `langchain-agents-observability` |

## Mental model

Three layers in the modern stack:

1. **`create_agent(model, tools, middleware=...)`** — the v1 default for building agents. Middleware is how you add retries, fallbacks, summarization, HITL, PII handling, call limits. Read the **middleware** skill for the production stack.
2. **Raw LangGraph (`StateGraph`)** — drop down when `create_agent` isn't enough (multi-graph workflows, custom state, parallel branches). Read **langgraph-code**.
3. **DeepAgents** — `create_deep_agent(...)` is `create_agent(...)` pre-loaded with `FilesystemMiddleware` + `SubAgentMiddleware` + `TodoListMiddleware`. Read **deepagents-code**.

For non-agentic flows (RAG, classification), use plain LCEL chains — middleware does **not** apply to chains.

## Common commands by lifecycle stage

| Stage | Command(s) |
|---|---|
| Scaffold a LangGraph project | `langgraph new my-agent --template react-agent` |
| Scaffold a DeepAgent / chain | No scaffolder — write a small `agent.py` (see scaffold skill) |
| Install deps | `pip install -e .` or `uv sync` |
| Iterate on a graph | `langgraph dev` |
| Run an agent ad hoc | `python -c "from agent.agent import agent; print(agent.invoke({'messages': [...] }))"` |
| Run evals | `python evals/run.py` |
| Unit-test agents (no API calls) | `pytest` with `LLMToolEmulator` middleware |
| Deploy to LangSmith Cloud | `langgraph build -t my-agent && langgraph deploy` |
| Deploy to Cloud Run | `gcloud run deploy my-agent --source .` |
| Deploy as a Docker image | `docker build && docker run --env-file .env` |

## Hard rules

- **Look up exact APIs via `mcpdoc`, don't guess.** If `mcpdoc` isn't configured, ask the user to set it up (see this repo's README) before you write LangChain code.
- **Always check what's already installed before suggesting `pip install`** — `pip show langchain langgraph deepagents langsmith`.
- **Never print `.env` contents** — refer to keys by name only.
- **For ANY production agent, add the production middleware stack** (call limits, retries, fallback, summarization). Copy-paste-ready in the middleware skill.
- **Run smoke evals before any deploy.** Not enforced — you must do it.
- **Read the project structure first** (`ls`, `tree -L 2`) before assuming layout.

## Required environment variables (most projects)

- `LANGSMITH_API_KEY` — for tracing and evals.
- `LANGSMITH_TRACING=true` — enables trace capture.
- `LANGSMITH_PROJECT` — trace bucket name.
- One of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

If any are missing when needed, fail fast with a clear message that names the missing variable.
