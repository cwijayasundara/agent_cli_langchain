# Pivot: from `lcagents` Python CLI to skills-only bundle

**Status:** Approved 2026-04-27
**Supersedes (in part):** `2026-04-27-langchain-agents-cli-design.md`
**Author:** Chaminda Wijayasundara

## Why this pivot

Initial design (the v1 spec) built a full Python CLI plus a skill bundle, modeled on Google's `agents-cli`. After v1 shipped, we re-examined the public shape of `agents-cli` itself: its repo contains skills, docs, and `.github/`. **No Python source.** The CLI binary is published to PyPI as a pre-built wheel built from a separate (private) tree.

The v1 design rationale leaned on a misread of agents-cli's positioning. Once corrected, the calculus changes:

- The user-facing artifact is the **skill bundle** — markdown that teaches Claude / Codex how to drive existing tools well.
- Building, shipping, and maintaining a Python implementation duplicates work already done by the LangChain ecosystem (`langgraph-cli`, `deepagents`, `langsmith`, `gcloud`, `docker`).
- A skills-only repo has no PyPI release pipeline, no version-pin maintenance against three rapidly-evolving frameworks, no backward-compat surface to defend.

The v1 implementation is preserved at git tag `v1-implementation-archive`. Recoverable if the calculus shifts again.

## What this repo becomes

A pure **skill bundle** that teaches a coding agent (Claude Code, Codex) how to scaffold, run, evaluate, and deploy LangChain / LangGraph / DeepAgents projects using the existing official tools. No Python code. No CLI binary. No PyPI release.

## Repo layout (after pivot)

```
agent_cli_langchain/
├── README.md                                 # rewritten — skill bundle positioning
├── CONTRIBUTING.md                           # new — how to propose / edit skills
├── LICENSE                                   # unchanged (Apache-2.0)
├── .gitignore                                # slimmed (no .venv / .pytest_cache)
├── skills/                                   # the deliverable
│   ├── langchain-agents-workflow.md
│   ├── langchain-agents-scaffold.md
│   ├── langchain-agents-langgraph-code.md
│   ├── langchain-agents-deepagents-code.md
│   ├── langchain-agents-langchain-code.md
│   ├── langchain-agents-langsmith-evals.md
│   ├── langchain-agents-deploy.md
│   └── langchain-agents-observability.md
└── docs/superpowers/                         # design + execution history
    ├── specs/2026-04-27-langchain-agents-cli-design.md      # v1 design (superseded for impl)
    ├── specs/2026-04-27-pivot-to-skills-only.md             # this doc
    └── plans/2026-04-27-langchain-agents-cli.md             # v1 execution log
```

## Removed

- `src/` — entire Python package tree (cli, commands, scaffold, templating, upgrade, config, coding_agents, four template directories, project_skills).
- `tests/` — entire test suite + integration tests + fixtures.
- `pyproject.toml` — no package to publish.

## Skill catalog (8 files)

All under `skills/`, prefix `langchain-agents-` so installed skills are namespaced and don't collide with other skill bundles. Each skill file MUST start with YAML frontmatter:

```yaml
---
name: <kebab-case-name>
description: <one-line trigger description>
---
```

| Skill | What it teaches |
|---|---|
| `langchain-agents-workflow` | Lifecycle entry point: scaffold → install → run → eval → deploy. Maps each step to the right external tool. Always-on. |
| `langchain-agents-scaffold` | `langgraph new <template>` for graph projects (covers langgraph-cli's templates). For DeepAgents and LCEL chains: minimal-code recipes (~10–15 lines). |
| `langchain-agents-langgraph-code` | LangGraph API patterns: StateGraph, nodes, edges, conditional routing, ToolNode, checkpointers, streaming. |
| `langchain-agents-deepagents-code` | DeepAgents API: `create_deep_agent`, sub-agents (`task` tool), built-ins (write_todos, virtual FS), customization. |
| `langchain-agents-langchain-code` | LCEL composition: `RunnableLambda`, `RunnableParallel`, `RunnablePassthrough`, retrieval pattern. |
| `langchain-agents-langsmith-evals` | Authoring evalsets (JSONL shape), writing evaluators (correctness, trajectory, latency, token_cost), running with `langsmith.evaluate(...)` Python API, comparing runs. |
| `langchain-agents-deploy` | Three deploy targets, each a self-contained recipe: **LangSmith Cloud** (`langgraph build && langgraph deploy`), **Cloud Run** (`gcloud run deploy --source` with IAM-gated default + Secret Manager), **Docker** (multi-stage Dockerfile + `docker build` + `docker run --env-file`). Smoke-test pre-flight is a recommended pattern (the agent runs the user's eval before deploying), not enforced. |
| `langchain-agents-observability` | LangSmith env vars (`LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_PROJECT`), trace reading, common failure-mode diagnostics. |

## Key design decisions in the new shape

1. **No canonical project layout.** The v1 design's biggest win was forcing one shape across all templates so skills could assume `agent/agent.py` exports `agent`. That's gone. Each official tool has its own conventions (`langgraph new`'s output shape varies by template; DeepAgents has no scaffolder; LCEL chains are bespoke). The skills must teach the agent to *adapt to whatever shape exists*, not enforce one. This is a real cost — accepted as the price of skills-only.

2. **No smoke-test gate.** The v1 deploy gate (refuse to deploy if `evals/run.py --smoke` fails) was CLI-enforced. Now it's a *recommendation* in the deploy skill. The coding agent decides whether to run evals before deploying. Real cost; accepted.

3. **Cloud Run is one section in the deploy skill, not a command.** All the design from the in-progress Cloud Run brainstorm (IAM-gated default, Secret Manager naming convention, pre-flight checks, `--source` flag) survives — but as guidance text in `langchain-agents-deploy.md`, not as Python code in `commands/deploy.py`.

4. **Skills installed via the same mechanism agents-cli uses.** `npx skills add <repo>` (or manual copy into `~/.claude/skills/` and `~/.codex/skills/`) — no Python `setup` command needed.

## Non-goals (explicit)

- Any Python code in this repo.
- A PyPI package.
- A CLI binary (`lcagents` or otherwise).
- A canonical scaffolded project layout.
- Skill installation tooling beyond the existing `npx skills add` ecosystem.
- Cursor / Gemini CLI / Antigravity skills (deferred — same as v1 §3).

## Migration / continuity

- The v1 implementation is preserved at git tag `v1-implementation-archive`. To recover: `git checkout v1-implementation-archive`.
- Existing v1 design and plan documents stay in `docs/superpowers/` as historical record.
- The pivot is a single commit on `master` so the diff is reviewable.

## Out of scope for this work order

- Publishing to a skills marketplace or registry.
- Auto-installation tooling.
- Skill versioning beyond what `git tag` provides.
- Cloud Run as a discrete `lcagents` command (it's a recipe in the deploy skill).
