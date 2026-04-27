---
name: langchain-agents-workflow
description: Use when starting work on any LangChain / LangGraph / DeepAgents project. Entry point for the develop -> evaluate -> deploy lifecycle, mapping each step to the right official tool.
---

# LangChain Agents Workflow

This skill teaches you (the coding agent) how to build, evaluate, and deploy LangChain ecosystem projects using the official tools. It is the entry point — read this first, then load the more specific skill for the step you're on.

There is **no `lcagents` binary** and no canonical project layout. You'll work directly with `langgraph-cli`, the `deepagents` package, the `langsmith` Python SDK, and the user's chosen deploy tool (`gcloud`, `docker`, etc.).

## When to load which skill

| Goal | Skill to load |
|---|---|
| Start a new agent project | `langchain-agents-scaffold` |
| Add nodes/edges/tools to a LangGraph agent | `langchain-agents-langgraph-code` |
| Customize a DeepAgent (sub-agents, tools, prompt) | `langchain-agents-deepagents-code` |
| Build a non-agentic LCEL pipeline (chains, RAG) | `langchain-agents-langchain-code` |
| Write or run evals | `langchain-agents-langsmith-evals` |
| Deploy to LangSmith Cloud, Cloud Run, or Docker | `langchain-agents-deploy` |
| Debug a misbehaving agent / read traces | `langchain-agents-observability` |

## Common commands by lifecycle stage

| Stage | Command(s) |
|---|---|
| Scaffold a LangGraph project | `langgraph new my-agent --template react-agent` (or another template — see scaffold skill) |
| Scaffold a DeepAgent | No scaffolder exists — `pip install deepagents` then write a small `agent.py` (see scaffold skill) |
| Scaffold a chain | No scaffolder exists — write a small `agent.py` using LCEL (see scaffold skill) |
| Install deps | `pip install -e .` or `uv sync` (depending on the project) |
| Iterate on a graph | `langgraph dev` (interactive UI + hot reload) |
| Run a chain or DeepAgent ad hoc | `python -c "from agent.agent import agent; print(agent.invoke({'messages':[{'role':'user','content':'hi'}]}))"` |
| Run evals | `python -c "from langsmith import evaluate; ..."` (see evals skill) |
| Deploy to LangSmith Cloud | `langgraph build -t my-agent && langgraph deploy` |
| Deploy to Cloud Run | `gcloud run deploy my-agent --source .` (see deploy skill for full setup) |
| Deploy as a Docker image | `docker build -t my-agent . && docker run --env-file .env my-agent` |

## Hard rules

- **Always check what's already installed before suggesting `pip install`.** `pip show langgraph deepagents langchain langsmith` first.
- **Never print `.env` contents** to the user or to logs. Refer to keys by name only.
- **Verify every install / build / deploy step** with the relevant `--version`, `--help`, or trace URL — do not assume success.
- **The recommended pre-flight before any deploy** is to run the user's evals (or at minimum a one-shot `agent.invoke(...)`). The deploy skill explains the smoke-test pattern. It is not enforced by any tool; you must do it.
- **Read the project structure first** (`ls`, `tree -L 2`) before assuming layout. Nothing here mandates a canonical shape.

## Required environment variables (most projects)

- `LANGSMITH_API_KEY` — for tracing and evals.
- `LANGSMITH_TRACING=true` — enables trace capture.
- `LANGSMITH_PROJECT` — trace bucket name.
- One of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. — depends on the model the agent uses.

If any are missing when needed, fail fast with a clear message that names the missing variable. Don't silently proceed.
