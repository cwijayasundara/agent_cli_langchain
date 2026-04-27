# `langchain-agents` skills

A skill bundle that turns Claude Code, Codex, and other coding agents into expert builders of LangChain / LangGraph / DeepAgents projects.

> **There is no CLI binary in this repo.** This is a pure skill bundle. The skills teach a coding agent how to drive the official tools (`langgraph-cli`, `deepagents`, `langsmith`, `gcloud`, `docker`) directly. Inspired by — and structurally modeled on — Google's [`agents-cli`](https://github.com/google/agents-cli).

## Install

### Using `npx skills`

```bash
npx skills add cwijayasundara/agent_cli_langchain
```

This copies the eight skill files into the skill directories of every coding agent it detects (`~/.claude/skills/`, `~/.codex/skills/`, etc.).

### Manual install

```bash
git clone https://github.com/cwijayasundara/agent_cli_langchain
cp agent_cli_langchain/skills/*.md ~/.claude/skills/
cp agent_cli_langchain/skills/*.md ~/.codex/skills/
```

## What the skills cover

| Skill | What your coding agent learns |
|---|---|
| `langchain-agents-workflow` | The full lifecycle and which official tool to reach for at each step. Always-on entry point. |
| `langchain-agents-scaffold` | `langgraph new` for graph projects; minimal recipes for DeepAgents and LCEL chains. |
| `langchain-agents-langgraph-code` | LangGraph API patterns: `StateGraph`, conditional routing, checkpointers, streaming. |
| `langchain-agents-deepagents-code` | DeepAgents API: `create_deep_agent`, sub-agents, virtual filesystem, built-ins. |
| `langchain-agents-langchain-code` | LCEL composition for chains and RAG. |
| `langchain-agents-langsmith-evals` | Evalset format, evaluators, running with `langsmith.evaluate(...)`, comparing runs. |
| `langchain-agents-deploy` | Three full deploy recipes: LangSmith Cloud, Google Cloud Run (`--source` + Secret Manager), self-hosted Docker. |
| `langchain-agents-observability` | LangSmith tracing setup and a failure-mode lookup table. |

## How to use

1. Install the skills (above).
2. Open your coding agent (Claude Code / Codex / etc.).
3. Ask it to do something — e.g.:
   - *"Scaffold a LangGraph agent that summarizes RSS feeds."*
   - *"Add a sub-agent to my DeepAgent that does web search."*
   - *"Deploy this agent to Cloud Run as an IAM-gated service."*
4. The coding agent loads the relevant skill and drives the official tools to do the work.

## What this is not

- **Not a CLI.** No `lcagents` or similar binary to install.
- **Not a scaffolder.** It teaches your coding agent to use `langgraph new` (and write a few lines for DeepAgents / LCEL); it doesn't ship its own templates.
- **Not a wrapper around the LangChain ecosystem.** Skills point at the existing official tools and explain how to use them well.
- **Not a published Python package.** Nothing on PyPI.

## Design

- High-level positioning: [`docs/superpowers/specs/2026-04-27-pivot-to-skills-only.md`](docs/superpowers/specs/2026-04-27-pivot-to-skills-only.md)
- Original v1 design (a Python CLI; superseded): [`docs/superpowers/specs/2026-04-27-langchain-agents-cli-design.md`](docs/superpowers/specs/2026-04-27-langchain-agents-cli-design.md)
- The v1 implementation lives at git tag `v1-implementation-archive`. Recoverable if needed.

## License

Apache-2.0. See [LICENSE](LICENSE).
