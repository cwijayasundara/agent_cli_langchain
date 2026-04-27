# `langchain-agents-cli` (`lcagents`) — Design Spec

**Status:** Draft v1
**Date:** 2026-04-27
**Author:** Chaminda Wijayasundara (cwijay@biz2bricks.ai), via brainstorming session

## 1. Summary

`lcagents` is a Python CLI plus a bundle of skills that turns Claude Code and Codex into expert builders of LangChain / LangGraph / DeepAgents projects. It is modeled directly on Google's `agents-cli`: **a tool *for* coding agents, not a coding agent itself.** It scaffolds projects with a single canonical layout, ships skills the coding agent reads to know how to work in that layout, and provides the commands (`run`, `dev`, `eval`, `deploy`) the coding agent needs to execute and validate its work.

The output of `lcagents scaffold` is a project the coding agent can immediately reason about because the skill files in `.agents/skills/` describe its exact shape. The output of `lcagents deploy` is a running agent on either LangSmith Cloud or in a Docker container.

## 2. Goals

1. Give a coding agent (Claude Code or Codex) one consistent mental model for any LangChain-based agent project, regardless of which framework (LangGraph, DeepAgents, plain LangChain) the user picked.
2. Take a user from `lcagents scaffold my-agent` to a deployed, traced, evaluated agent in a single coherent CLI surface.
3. Stay out of the coding agent's way: no TUI, no chat loop, no decisions the coding agent should be making.
4. Smoke-test before deploying — never let an agent ship if it can't answer its own example dataset.

## 3. Non-Goals (v1)

- Cursor, Gemini CLI, Antigravity skill installation. Deferred to v1.1.
- Cloud Run, AWS Lambda, Kubernetes deploy targets. Deferred; can be added via `enhance --add <target>`.
- A data-ingestion / RAG pipeline command. LangChain has its own loader story; we don't replicate it.
- A TUI or interactive chat REPL. We are the antithesis of a coding agent.
- Multi-project monorepo support. One project per repo.
- Wrapping `langgraph-cli` 1:1. We delegate to it for `dev` only; project shape is ours.

## 4. Positioning vs. neighboring tools

| Tool | What it does | Relationship to `lcagents` |
|---|---|---|
| `agents-cli` (Google) | Same model, ADK on Google Cloud | Direct inspiration; we copy the model, not the framework. |
| `langgraph-cli` | Templates + dev server + LangSmith Cloud deploy | We delegate `dev` and `deploy langsmith` to it; we own scaffold layout, eval harness, docker target, skills. |
| DeepAgents CLI | Standalone terminal coding agent built on DeepAgents | Different product entirely. We *scaffold* DeepAgent projects; we don't compete with their CLI. |
| LangSmith | Tracing, evals, managed deploy | We integrate with it; eval and observability skills assume LangSmith. |

## 5. Command Surface

```
# Setup
lcagents setup                    # install CLI + skills into Claude Code & Codex
lcagents login                    # configure LangSmith / provider API keys (.env)
lcagents login --status
lcagents info                     # project + CLI version + detected coding agents

# Scaffold
lcagents scaffold <name> --template {langgraph-agent|deep-agent|langchain-chain}
lcagents scaffold enhance         # add deploy / docker / eval to existing project
lcagents scaffold upgrade         # bump skills + template files to current version

# Develop
lcagents install                  # uv sync
lcagents run "prompt"             # headless one-shot of the scaffolded agent
lcagents dev                      # delegates to `langgraph dev` for graph templates
lcagents lint                     # ruff + mypy

# Evaluate
lcagents eval run                 # run LangSmith evalsets against the local agent
lcagents eval compare a.json b.json

# Deploy
lcagents deploy langsmith         # langgraph build + push to LangSmith Cloud
lcagents deploy docker            # build self-contained image (FastAPI host)
```

`run` is what makes us more than a pure agents-cli clone: it loads the user's scaffolded agent and invokes it once. CI uses it, the coding agent uses it post-scaffold to confirm the project starts.

## 6. The Runnable Contract

Every template's `agent/agent.py` exports a symbol named `agent` that satisfies LangChain's `Runnable` interface (`.invoke`, `.ainvoke`, `.stream`, `.astream`). LangGraph compiled graphs, DeepAgents, and LCEL chains all already satisfy this — the contract is free, not invented.

`lcagents run`, `server/app.py`, and `evals/run.py` all consume this one contract:

```python
from agent.agent import agent
result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
```

The skills teach the coding agent: **never rename `agent`**.

## 7. Scaffolded Project Layout

One canonical layout across all three templates. Only the `agent/` subtree differs.

```
my-agent/
├── pyproject.toml              # uv-managed
├── uv.lock
├── .env.example                # OPENAI_API_KEY, ANTHROPIC_API_KEY, LANGSMITH_*
├── .gitignore
├── README.md
├── CLAUDE.md                   # points Claude Code at .agents/skills/
├── AGENTS.md                   # same content for Codex
├── .claude/
│   └── settings.json           # post-edit hook: `lcagents lint` on agent/**
├── .agents/
│   ├── skills/                 # project-local skill copies (template-specific subset)
│   │   ├── project-overview.md
│   │   ├── adding-a-tool.md
│   │   ├── adding-a-subagent.md      # deep-agent only
│   │   ├── editing-the-graph.md      # langgraph-agent only
│   │   ├── editing-the-chain.md      # langchain-chain only
│   │   ├── writing-evals.md
│   │   └── deploying.md
│   └── lcagents.toml           # template name, scaffolder version, deploy target, eval config
├── agent/
│   ├── __init__.py
│   ├── agent.py                # exports `agent` — the runnable artifact
│   ├── tools.py
│   ├── prompts.py
│   └── (graph.py | subagents.py | chain.py)
├── evals/
│   ├── datasets/
│   │   └── smoke.jsonl         # 3 example inputs to start
│   ├── evaluators.py           # LangSmith evaluators
│   └── run.py
├── server/
│   ├── app.py                  # FastAPI; POST /invoke, POST /stream
│   └── Dockerfile              # multi-stage; uv sync --frozen
├── langgraph.json              # for `langgraph dev` / LangSmith Cloud
└── tests/
    └── test_agent.py
```

**Why a single layout across templates:** the coding agent's mental model is the bottleneck. A skill that says "tools live in `agent/tools.py`" is sharper than one that says "tools live in `agent/tools.py` for LangGraph but `agent/chain_tools.py` for chains." The cost is template author discipline; the win is skill quality.

**Why skills are *copied into* the project, not just installed globally:** matches `agents-cli`'s model. The coding agent sees skills in the repo it's working in, no global registry lookup. `scaffold upgrade` re-syncs.

**Why `langgraph.json` is included even for non-graph templates:** DeepAgents returns a compiled graph; chains can be wrapped. Including the file means LangSmith Cloud deploy works uniformly.

## 8. Skill Catalog

**Global skills** (installed to `~/.claude/skills/` and `~/.codex/skills/` by `lcagents setup`):

| Skill | Purpose |
|---|---|
| `lcagents-workflow` | Lifecycle: scaffold → run → eval → deploy. Always-on entry point. |
| `lcagents-scaffold` | How to invoke `lcagents scaffold`, picking templates, what `enhance`/`upgrade` do. |
| `lcagents-langgraph-code` | LangGraph API: `StateGraph`, nodes, edges, conditional routing, checkpointers, streaming. |
| `lcagents-deepagents-code` | DeepAgents API: `create_deep_agent`, sub-agents, `task` tool, virtual FS, planning. |
| `lcagents-langchain-code` | LCEL, retrievers, embeddings, chat models — for the chain template. |
| `lcagents-eval` | LangSmith evalsets, evaluator selection, interpreting `eval compare` output. |
| `lcagents-deploy` | Picking between `langsmith` and `docker`, secrets, env vars, smoke testing. |
| `lcagents-observability` | LangSmith tracing setup, reading traces, common failure patterns. |

**Project-local skills** (copied into `.agents/skills/` by `lcagents scaffold`, subset per template):

| Skill | When included |
|---|---|
| `project-overview` | Always. Names the template, points at `agent/agent.py`, lists commands. |
| `editing-the-graph` | `langgraph-agent` only. |
| `adding-a-subagent` | `deep-agent` only. |
| `editing-the-chain` | `langchain-chain` only. |
| `adding-a-tool` | Always. |
| `writing-evals` | Always. |
| `deploying` | Always. |

`CLAUDE.md` and `AGENTS.md` are siblings with identical content pointing at `.agents/skills/`.

## 9. Coding-Agent Integration

`lcagents setup`:

1. Detects `~/.claude/` and `~/.codex/` (and similar) directories.
2. Writes the eight global skill `.md` files into each detected coding-agent's skills directory.
3. Records install location + CLI version in `~/.config/lcagents/install.json` so `update` and `upgrade` work.
4. No `npx` dependency. Pure Python.

`scaffold` writes (in addition to project files):

- `CLAUDE.md` and `AGENTS.md` with identical content.
- `.claude/settings.json` with a post-edit hook on `agent/**` that runs `lcagents lint`.
- `.agents/skills/` with the template-specific subset of project-local skills.

## 10. Eval

`lcagents eval run`:

- Executes the project's `evals/run.py` as a subprocess (so users can also run `python evals/run.py` directly without the CLI).
- `evals/run.py` (scaffolded into every project) reads `evals/datasets/*.jsonl` (one JSON object per line: `{"input": {...}, "reference": "..."}`, `reference` optional), reads `evals/evaluators.py` for a list of LangSmith evaluator callables, and calls `langsmith.evaluate()`.
- Defaults shipped in `evals/evaluators.py`: `correctness` (LLM-as-judge against reference), `trajectory` (expected tool calls fired), `latency`, `token_cost`.
- Results land in LangSmith *and* are written to `evals/results/<timestamp>.json`.
- `LANGSMITH_API_KEY` required; the CLI checks before invoking the subprocess and fails fast with a clear message.
- `lcagents eval run --smoke` runs only the `evals/datasets/smoke.jsonl` rows; this is the dataset deploy commands gate on.

`lcagents eval compare a.json b.json` prints a metric-delta table — the coding agent uses this to verify changes don't regress.

## 11. Deploy

### `lcagents deploy langsmith`

1. Pre-flight: `lcagents eval run --smoke` (the 3-row smoke dataset). Refuse to deploy on failure.
2. Wrap `langgraph build` + `langgraph deploy` against `langgraph.json`.
3. Push secrets from `.env` to LangSmith via the LangSmith API.
4. Post-deploy: hit the deployed `/invoke` with the smoke prompt; print the trace URL.

### `lcagents deploy docker`

1. Pre-flight: same smoke-eval gate.
2. Build the multi-stage image:
   - **Build stage:** `uv sync --frozen` against `pyproject.toml` + `uv.lock`.
   - **Runtime stage:** slim Python base + the venv + source. Non-root user.
3. Optional `--push registry/...` to push.
4. Post-build: spin the container locally on a random port, hit `/invoke` with the smoke prompt, tear down.
5. Print the `docker run -e ...` invocation the user needs (does **not** bake secrets into the image).

### `server/app.py`

A ~30-line FastAPI app: `POST /invoke` and `POST /stream` that proxy to the imported `agent`. No LangServe dep — its deprecation status is unclear; FastAPI directly is safer.

## 12. `enhance` and `upgrade`

`lcagents scaffold enhance`:

- `--add docker` — drops in `server/` + `Dockerfile` if missing.
- `--add evals` — drops in `evals/` scaffolding if missing.
- `--target {langsmith|docker}` — switches default deploy target in `lcagents.toml`.

`lcagents scaffold upgrade`:

- Reads scaffolder version from `lcagents.toml`.
- 3-way merge between (recorded baseline, current project state, new template) for: `.agents/skills/`, `CLAUDE.md`, `AGENTS.md`, `server/Dockerfile`, `pyproject.toml` pin ranges.
- Conflicts written as `<file>.lcagents-upgrade.txt` next to the original. The coding agent is taught (via the `lcagents-scaffold` skill) to resolve them.

## 13. Implementation

### Repo layout (this repo)

```
agent_cli_langchain/
├── pyproject.toml              # Python 3.11+, hatchling
├── README.md
├── src/
│   └── lcagents/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py              # Typer app, command groups
│       ├── commands/
│       │   ├── setup.py
│       │   ├── login.py
│       │   ├── scaffold.py
│       │   ├── run.py
│       │   ├── dev.py
│       │   ├── eval.py
│       │   ├── deploy.py
│       │   ├── lint.py
│       │   └── info.py
│       ├── templates/          # Jinja2 templates, one dir per template
│       │   ├── _shared/
│       │   ├── langgraph-agent/
│       │   ├── deep-agent/
│       │   └── langchain-chain/
│       ├── skills/             # global skills (shipped to coding agents)
│       ├── project_skills/     # project-local skills
│       ├── upgrade.py          # 3-way merge
│       ├── coding_agents.py    # detect/install for Claude Code, Codex
│       └── config.py           # read/write .agents/lcagents.toml
└── tests/
    ├── test_scaffold.py
    ├── test_run.py
    ├── test_eval.py
    ├── test_deploy_docker.py
    └── test_upgrade.py
```

### Tech choices

| Choice | Rationale |
|---|---|
| Typer | Type-hint-first CLI; LangChain ecosystem norm. |
| Jinja2 | Boring, proven, every Python dev knows it. |
| `uv` (in scaffolded projects) | Fastest; LangChain examples default to it. |
| stdlib `tomllib` + `tomli_w` | No extra dep on Python 3.11+. |
| `questionary` | Better interactive UX than raw `input()`. |
| `httpx` | Already a transitive dep of `langsmith`. |
| `docker` Python SDK | Talks to local Docker socket; degrades gracefully. |
| Pytest + `pytest-docker` | For deploy-docker integration test. |

**No runtime dep on `langchain` / `langgraph` / `deepagents` in the CLI itself.** We shell out to user-installed versions inside scaffolded projects. The CLI doesn't constrain framework upgrades.

### Distribution

- PyPI: `langchain-agents-cli` (binary `lcagents`).
- `uvx langchain-agents-cli setup` works out of the box.
- SemVer; version recorded in every scaffolded `lcagents.toml`.

## 14. Out-of-scope (explicit)

See §3. Items deferred to v1.1+: Cursor / Gemini CLI / Antigravity skills, Cloud Run / Lambda / K8s deploy, RAG ingestion command, multi-project monorepos, TUI/REPL.

## 15. Open questions for implementation phase

- Exact `langgraph` / `deepagents` version pins for each template's `pyproject.toml` (pick at implementation time against then-current versions).
- Whether the LangSmith deploy path should auto-create the LangSmith project if it doesn't exist, or fail with a clear message.
- Whether `lcagents update` (force-reinstall global skills) should be its own command or just `setup --force`. Probably the latter.
