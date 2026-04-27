---
name: langchain-agents-workflow
description: Use when starting work on any LangChain / LangGraph / DeepAgents project. Entry point for the develop -> middleware -> evaluate -> deploy lifecycle, mapping each step to the right official tool.
---

# LangChain Agents Workflow

This skill teaches you (the coding agent) how to build, productionise, evaluate, and deploy LangChain ecosystem projects using the official tools. It is the entry point — read this first, then load the more specific skill for the step you're on.

There is **no `lcagents` binary** and no canonical project layout. You'll work directly with `langchain` (`create_agent`), `langgraph-cli`, the `deepagents` package, the `langsmith` Python SDK, and the user's chosen deploy tool (`gcloud`, `docker`, etc.).

## When to load which skill

| Goal | Skill |
|---|---|
| Start a new agent project | `langchain-agents-scaffold` |
| Build a modern agent (most cases) | `langchain-agents-middleware` ← first; uses `create_agent(...)` with middleware |
| Add nodes/edges/tools to a custom LangGraph | `langchain-agents-langgraph-code` |
| Customize a DeepAgent (sub-agents, tools, prompt) | `langchain-agents-deepagents-code` |
| Build a non-agentic LCEL pipeline (chains, RAG, structured output) | `langchain-agents-langchain-code` |
| Write or run evals; unit/integration test agents | `langchain-agents-langsmith-evals` |
| Deploy + productionise (durable execution, checkpointer, scaling) | `langchain-agents-deploy` |
| Debug a misbehaving agent / read traces / OTEL | `langchain-agents-observability` |

## Mental model

There are **three layers** in the modern stack:

1. **Composition primitive: `create_agent(model, tools, middleware=...)`** — the v1 default for building agents. Middleware is how you add retries, fallbacks, summarization, HITL, PII handling, call limits, etc. Read the **middleware** skill for the production stack.
2. **Underlying graph: LangGraph.** `create_agent` returns a compiled LangGraph; you can drop down to raw `StateGraph` when you need fine-grained control (custom routing, multi-graph workflows). Read the **langgraph-code** skill for that.
3. **Pre-composed agent: DeepAgents.** `create_deep_agent(...)` is `create_agent(...)` pre-loaded with `FilesystemMiddleware` + `SubAgentMiddleware` + `TodoListMiddleware`. Read the **deepagents-code** skill.

For non-agentic flows (RAG, summarisation, classification), use plain LCEL chains — middleware does **not** apply to chains; it's an agent-specific concept.

## Common commands by lifecycle stage

| Stage | Command(s) |
|---|---|
| Scaffold a LangGraph project | `langgraph new my-agent --template react-agent` |
| Scaffold a DeepAgent | No scaffolder — `pip install deepagents` then write a small `agent.py` |
| Scaffold a chain | No scaffolder — write a small `agent.py` using LCEL |
| Install deps | `pip install -e .` or `uv sync` |
| Iterate on a graph | `langgraph dev` (interactive UI + hot reload) |
| Run an agent ad hoc | `python -c "from agent.agent import agent; print(agent.invoke({'messages': [...] }))"` |
| Run evals | `python evals/run.py` (uses `langsmith.evaluate(...)`) |
| Unit-test agents (no API calls) | `pytest` with `LLMToolEmulator` middleware to fake tool calls |
| Deploy to LangSmith Cloud | `langgraph build -t my-agent && langgraph deploy` |
| Deploy to Cloud Run | `gcloud run deploy my-agent --source .` |
| Deploy as a Docker image | `docker build && docker run --env-file .env` |

## Hard rules

- **Always check what's already installed before suggesting `pip install`.** `pip show langchain langgraph deepagents langsmith` first.
- **Never print `.env` contents** to the user or to logs. Refer to keys by name only.
- **Verify every install / build / deploy step** with the relevant `--version`, `--help`, or trace URL — do not assume success.
- **For ANY production agent, add the production middleware stack** (call limits, retries, fallback, summarization). The middleware skill has the copy-paste-ready stack.
- **Run smoke evals before any deploy.** Not enforced — you must do it.
- **Read the project structure first** (`ls`, `tree -L 2`) before assuming layout. The ecosystem has multiple shapes; pick the matching skill.

## Required environment variables (most projects)

- `LANGSMITH_API_KEY` — for tracing and evals.
- `LANGSMITH_TRACING=true` — enables trace capture.
- `LANGSMITH_PROJECT` — trace bucket name.
- One of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. — depends on the model.

If any are missing when needed, fail fast with a clear message that names the missing variable. Don't silently proceed.
