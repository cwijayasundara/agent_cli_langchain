# langchain-agents-cli (`lcagents`)

A tool *for* coding agents (Claude Code, Codex), not a coding agent itself. Scaffolds, runs, evaluates, and deploys LangChain / LangGraph / DeepAgents projects.

## Install

    uvx langchain-agents-cli setup
    # or, in a venv:
    pip install langchain-agents-cli && lcagents setup

`setup` installs the lcagents skills into Claude Code (`~/.claude/skills/`) and Codex (`~/.codex/skills/`) if found.

## Scaffold a project

    lcagents scaffold create my-agent --template langgraph-agent
    cd my-agent
    lcagents install
    lcagents login        # populate .env
    lcagents run "hello"

Templates:
- `langgraph-agent` — explicit StateGraph
- `deep-agent` — DeepAgents (planning + sub-agents + virtual FS)
- `langchain-chain` — LCEL chain (RAG / non-agentic)

## Other commands

| Command | What it does |
|---|---|
| `lcagents dev` | Interactive LangGraph dev server |
| `lcagents eval run` | LangSmith evals |
| `lcagents eval compare` | Diff two eval result files |
| `lcagents deploy langsmith` | Push to LangSmith Cloud |
| `lcagents deploy docker --tag X` | Build a self-contained image |
| `lcagents scaffold enhance --add docker` | Add deploy to an existing project |
| `lcagents scaffold upgrade` | Re-sync skills/templates after a CLI bump |

## Design

See `docs/superpowers/specs/2026-04-27-langchain-agents-cli-design.md`.

## License

Apache-2.0.
