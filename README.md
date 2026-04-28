# `langchain-agents` skills

A skill bundle that turns Claude Code, Codex, and other coding agents into expert builders of LangChain / LangGraph / DeepAgents projects.

> **There is no CLI binary in this repo.** This is a pure skill bundle. The skills teach a coding agent how to drive the official tools (`langgraph-cli`, `deepagents`, `langsmith`, `gcloud`, `docker`) directly. Inspired by — and structurally modeled on — Google's [`agents-cli`](https://github.com/google/agents-cli).

## How it pairs with `mcpdoc`

This bundle is designed to be installed **alongside** [`langchain-ai/mcpdoc`](https://github.com/langchain-ai/mcpdoc) — the official MCP server that exposes live LangChain documentation. The two have distinct roles:

| | `mcpdoc` | This bundle |
|---|---|---|
| Role | Live API reference | Opinionated playbook |
| Content | Always-current `docs.langchain.com` pages, fetched on demand | Production patterns, gotchas, integrated recipes (Cloud Run + Postgres + middleware), failure-mode tables |
| Drift risk | Zero — fetched live | Slow drift on editorial content; we maintain |

`mcpdoc` answers *"what's the API right now?"*. The bundle answers *"how should I think about building this?"*. Use both. Skills explicitly point at `mcpdoc` URLs for API lookups.

## Install both

### 1. The skill bundle

```bash
npx skills add cwijayasundara/agent_cli_langchain
```

Or manually:

```bash
git clone https://github.com/cwijayasundara/agent_cli_langchain
cp -R agent_cli_langchain/skills/* ~/.claude/skills/
cp -R agent_cli_langchain/skills/* ~/.codex/skills/
```

### 2. The `mcpdoc` MCP server

[`langchain-ai/mcpdoc`](https://github.com/langchain-ai/mcpdoc) is an MCP server that exposes `llms.txt` indices to coding agents. The agent gets two tools: `list_doc_sources()` (lists what's indexed) and `fetch_docs(url)` (fetches a URL listed in any registered `llms.txt`). Fetches are live — docs are always current.

**Prerequisites:** [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (`uvx` ships with it). `pipx` works too if you prefer — substitute `pipx run mcpdoc` for `uvx --from mcpdoc mcpdoc` in the command below.

**Install for Claude Code** (recommended config — single consolidated docs index):

```bash
claude mcp add-json langchain-docs '{
  "command": "uvx",
  "args": [
    "--from", "mcpdoc", "mcpdoc",
    "--urls", "LangChain:https://docs.langchain.com/llms.txt",
    "--transport", "stdio"
  ]
}'
```

**Verify it loaded:**

```bash
claude mcp list
# expected output includes: langchain-docs: uvx --from mcpdoc mcpdoc ... - ✓ Connected
```

If you see `✗ Failed to connect`, the most common causes are: `uvx` not on `PATH` (install `uv` first); the LangChain docs site temporarily 5xx'ing (retry); a typo in the `--urls` argument (the syntax below is strict).

**`--urls` syntax is strict.** It takes a *single string* with space-separated `Name:URL` pairs. NOT one arg per source. To register multiple indices, concatenate them into one string:

```json
"--urls", "LangChain:https://docs.langchain.com/llms.txt LangGraph:https://langchain-ai.github.io/langgraph/llms.txt LangGraphJS:https://langchain-ai.github.io/langgraphjs/llms.txt"
```

The single `LangChain:https://docs.langchain.com/llms.txt` index above is the modern consolidated `docs.langchain.com` site — it covers LangChain, LangGraph, LangSmith, and DeepAgents docs in one index. The skills in this bundle point at `docs.langchain.com/...` URLs, so this is the index that pairs cleanly with them. The legacy per-package URLs (`python.langchain.com`, `langchain-ai.github.io/langgraph`) still work and are listed in the upstream `mcpdoc` README if you prefer that split.

**How this bundle uses `mcpdoc` at runtime:**

1. The agent loads a skill from this bundle (e.g. `langchain-agents-langgraph-code`).
2. The skill tells the agent: *"For API reference, fetch from `https://docs.langchain.com/oss/python/langgraph/...`."*
3. The agent calls `fetch_docs(url)` — `mcpdoc` returns the live page.
4. The agent combines the bundle's editorial guidance with the live API to write code.

Without `mcpdoc`, the agent has only the bundle's editorial content and falls back to its training-data memory of the LangChain API — which drifts as the ecosystem evolves. That's why we treat `mcpdoc` as a required companion, not optional.

**For Cursor / Windsurf / Claude Desktop**, see the [`mcpdoc` README](https://github.com/langchain-ai/mcpdoc#configuration) — it lists per-IDE config files. The `--urls` syntax is the same. After editing the IDE config, restart the IDE for it to pick up the new MCP server.

## What the skills cover

| Skill | What your coding agent learns |
|---|---|
| `langchain-agents-workflow` | Lifecycle entry point. Routes to other skills, explains how skills + `mcpdoc` divide labour. Always-on. |
| `langchain-agents-scaffold` | `langgraph new` for graph projects; minimal recipes for DeepAgents and LCEL chains. |
| `langchain-agents-middleware` | The agentic middleware system — the v1+ composition primitive. Built-ins (retries, fallbacks, summarization, HITL, PII, call limits) + custom middleware authoring + production stack. |
| `langchain-agents-langgraph-code` | Editorial: when to drop down to raw `StateGraph`, plus production rules of thumb for checkpointers and `thread_id`. Points at `mcpdoc` URLs for API reference. |
| `langchain-agents-deepagents-code` | Editorial: filesystem backend choice, sandboxed execution rules, sub-agent design. Points at `mcpdoc` for API reference. |
| `langchain-agents-langchain-code` | Editorial: LCEL vs `create_agent`, structured outputs, RAG production patterns. Points at `mcpdoc` for API reference. |
| `langchain-agents-langsmith-evals` | Evalset format, evaluators, runner script, plus three-layer testing strategy (unit / integration / pytest plugin). |
| `langchain-agents-deploy` | Productionisation (durable execution, production middleware stack, Postgres) + three deploy recipes (LangSmith Cloud, Cloud Run with Secret Manager, self-hosted Docker). |
| `langchain-agents-observability` | LangSmith tracing, OpenTelemetry, distributed tracing, alerting, sampling, failure-mode lookup table. |

## How to use

1. Install both the skill bundle and `mcpdoc` (above).
2. Open your coding agent.
3. Ask it to do something — e.g.:
   - *"Scaffold a LangGraph agent that summarizes RSS feeds."*
   - *"Add a sub-agent to my DeepAgent that does web search."*
   - *"Deploy this agent to Cloud Run as an IAM-gated service."*
4. The agent loads the relevant skill (this bundle) for *how to think*, fetches the exact API details from `mcpdoc` for *what to type*, and drives the official tools.

## What this is not

- **Not a CLI.** No binary to install.
- **Not a scaffolder.** It teaches the agent to use `langgraph new` and write a few lines for DeepAgents / LCEL.
- **Not a docs replacement.** That's `mcpdoc`'s job — install it.
- **Not a published Python package.** Nothing on PyPI.

## Design

A 27-slide design deck covering the technical details — middleware system, productionisation patterns, deploy recipes, the skills+`mcpdoc` runtime model, maintenance strategy — lives at [`design-deck.md`](design-deck.md). The file is markdown formatted for slide-by-slide import into Google Slides (instructions at the top of the file).

## History

This repo went through one earlier iteration as a full Python CLI before becoming a pure skill bundle. That implementation is preserved at git tag `v1-implementation-archive`. See `git log` for the design evolution.

## License

Apache-2.0. See [LICENSE](LICENSE).
