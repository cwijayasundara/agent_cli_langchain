# langchain-agents skills — Design Deck

> **How to use this file with Google Slides:**
> Each `## Slide N` heading is one slide. Three import options:
> 1. **`md2googleslides` CLI** (Node): `npm i -g md2googleslides && md2gslides design-deck.md` — uploads directly.
> 2. **Marp** (recommended): `npx @marp-team/marp-cli design-deck.md -o design-deck.pptx`, then File → Import slides in Google Slides.
> 3. **Manual**: open Google Slides, switch to outline view (View → Outline), paste each slide's title + bullets one at a time.
> Speaker-notes lines (`> Speaker notes:`) at the bottom of each slide are intended for the notes pane, not the slide body.

---

## Slide 1: langchain-agents skills

**A skill bundle for coding agents working on LangChain / LangGraph / DeepAgents projects.**

- 9 markdown skill files installed into Claude Code, Codex, etc.
- Pairs with the official `langchain-ai/mcpdoc` MCP server.
- Public: https://github.com/cwijayasundara/agent_cli_langchain
- Apache-2.0.

> Speaker notes: the deliverable is the skill bundle. No CLI binary, no PyPI package, no Python source — just curated markdown that turns a coding agent into a competent LangChain engineer.

---

## Slide 2: TL;DR

- **Problem:** coding agents (Claude Code, Codex) make predictable mistakes in LangChain projects — wrong scaffold path, no middleware, public Cloud Run, baked secrets.
- **Solution:** opinionated skill bundle teaching the agent how to *think* + `mcpdoc` for live API reference.
- **Won by:** 9 skills; `mcpdoc` companion; rename pivot from "Python CLI" to "skills-only" mid-build.
- **Status:** shipped to GitHub `main`; nothing on PyPI; v1 implementation preserved at git tag.

> Speaker notes: started as a Python CLI clone of Google's agents-cli, pivoted when we realised agents-cli's PUBLIC repo is itself skills+docs only. Pivot was deliberate; commit `10dc81e`.

---

## Slide 3: Inspiration — Google's `agents-cli`

- Google ships an `agents-cli` for ADK on Google Cloud.
- Public repo at `google/agents-cli`: contains `skills/`, `docs/`, `.github/`, README. **No Python source.**
- Implementation lives in their internal monorepo, ships as a pre-built wheel on PyPI.
- Tagline: *"a tool **for** coding agents, not a coding agent itself."*
- Our work mirrors the skills+docs model. We don't ship the CLI half (don't need to).

> Speaker notes: this distinction caused our mid-build pivot. We initially read agents-cli as "a CLI plus skills" and built both. Looking again, their PUBLIC artifact is just the skills.

---

## Slide 4: What's in scope

Three LangChain ecosystem frameworks, all on day one:

- **LangGraph** — full StateGraph control; the canonical agent framework.
- **DeepAgents** — `create_deep_agent(...)` with planning, sub-agents, virtual FS.
- **LangChain (LCEL)** — `Runnable` pipelines for RAG, classification, structured extraction.

Plus three deploy targets:
- LangSmith Cloud, Google Cloud Run, self-hosted Docker.

> Speaker notes: explicitly NOT in scope: Cursor / Gemini CLI / Antigravity skill installation (skills work via standard ~/.claude/skills/ and ~/.codex/skills/ paths anyway), AWS Lambda / Kubernetes deploy targets, RAG ingestion pipelines, multi-project monorepos, any TUI.

---

## Slide 5: Two complementary tools

| | `mcpdoc` (MCP server) | This bundle (skills) |
|---|---|---|
| **Role** | Live API reference | Opinionated playbook |
| **Content** | `docs.langchain.com` pages, fetched on demand | Production patterns, gotchas, integrated recipes |
| **Drift risk** | **Zero** — always live | Slow drift on editorial content; we maintain |
| **Answers** | "What's the signature of `SummarizationMiddleware`?" | "How should I think about building this?" |

`mcpdoc` is treated as a **required** companion, not optional. Skills explicitly point at `docs.langchain.com` URLs for API lookup.

> Speaker notes: this division is the design centerpiece. Without mcpdoc, skills would have to embed API reference content that ages with every LangChain release. With mcpdoc, we keep only non-rotting editorial content.

---

## Slide 6: The 9 skills

| Skill | Role |
|---|---|
| `langchain-agents-workflow` | Entry point; routes to other skills; explains skills+mcpdoc split |
| `langchain-agents-scaffold` | `langgraph new` + DeepAgent / LCEL recipes |
| `langchain-agents-middleware` | **Centerpiece.** v1+ composition primitive + production stack |
| `langchain-agents-langgraph-code` | When to drop down to raw `StateGraph` (editorial) |
| `langchain-agents-deepagents-code` | Filesystem backends, sandboxes, sub-agent design (editorial) |
| `langchain-agents-langchain-code` | LCEL vs `create_agent`, structured outputs, RAG (editorial) |
| `langchain-agents-langsmith-evals` | Evalsets, evaluators, three-layer testing |
| `langchain-agents-deploy` | Productionisation + 3 deploy targets |
| `langchain-agents-observability` | LangSmith + OTEL + failure-mode lookup |

> Speaker notes: ~1300 lines across 9 files. The three "code" skills are deliberately thin (45-90 lines each) and point at mcpdoc for API reference. The other six are substantive (100-400 lines each) — synthesis content not in any single doc page.

---

## Slide 7: Mental model — three layers

1. **`create_agent(model, tools, middleware=...)`** — v1 default for agents. Middleware adds retries, fallbacks, summarization, HITL, PII handling, call limits.
2. **Raw LangGraph (`StateGraph`)** — drop down for multi-graph workflows, custom routing, parallel branches, non-message state.
3. **DeepAgents** — `create_deep_agent(...)` is `create_agent(...)` pre-loaded with `FilesystemMiddleware` + `SubAgentMiddleware` + `TodoListMiddleware`.

For non-agentic flows (RAG, classification): plain LCEL chains. **Middleware does not apply to chains.**

> Speaker notes: the most common bug: agents try to bolt agentic behavior onto LCEL chains. The dividing line — does the LLM choose what happens next, or does the code? LLM = agents. Code = LCEL.

---

## Slide 8: Centerpiece — agentic middleware

Modern LangChain composition primitive (v1+). Not optional for production.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware, ToolCallLimitMiddleware,
    ModelRetryMiddleware, ToolRetryMiddleware,
    ModelFallbackMiddleware, SummarizationMiddleware,
    HumanInTheLoopMiddleware, PIIMiddleware,
)

agent = create_agent(
    model="claude-sonnet-4-6",
    tools=TOOLS,
    middleware=[ ... ],
)
```

`create_agent(...)` returns a compiled LangGraph. `.invoke`, `.stream`, `langgraph dev`, `langgraph build` all work.

> Speaker notes: middleware is the single most important production concept in LangChain v1+. The agent applies them in order; first middleware in the list is the outermost wrapper for `wrap_*` hooks.

---

## Slide 9: Lifecycle hooks

| Hook | Fires on | Purpose |
|---|---|---|
| `before_agent` | Once, run start | Init state |
| `before_model` | Each model call | Inspect / mutate state pre-call |
| `wrap_model_call` | Wraps each model call | Intercept (retry, fallback, fail-fast) |
| `after_model` | Each model response | Inspect / mutate state post-call |
| `wrap_tool_call` | Wraps each tool call | Intercept (auth, retry, emulate) |
| `after_agent` | Once, run end | Cleanup / final state |

Custom middleware: inherit from `AgentMiddleware`; override the hooks you need; declare custom state via `state_schema = MyState`.

> Speaker notes: wrap-style hooks compose like Python decorators. Order matters. Limits before retries; redaction before logging.

---

## Slide 10: Built-in middleware catalog

| Middleware | Purpose |
|---|---|
| `SummarizationMiddleware` | Auto-summarize long conversations |
| `HumanInTheLoopMiddleware` | Pause for approve/edit/reject (needs checkpointer) |
| `ModelCallLimitMiddleware` | Cap model calls (cost + infinite loop) |
| `ToolCallLimitMiddleware` | Cap tool calls (per-tool or global) |
| `ModelRetryMiddleware` | Retry transient model failures |
| `ToolRetryMiddleware` | Retry transient tool failures |
| `ModelFallbackMiddleware` | Fall back to alt models |
| `LLMToolSelectorMiddleware` | LLM picks which tools to expose |
| `PIIMiddleware` | Detect / redact / mask / block PII |
| `ContextEditingMiddleware` | Drop old tool outputs |
| `TodoListMiddleware` | Adds `write_todos` planning tool |
| `LLMToolEmulator` | Fake tool execution (TESTING ONLY) |

DeepAgents adds: `FilesystemMiddleware`, `SubAgentMiddleware`.

> Speaker notes: ~14 built-in middlewares cover most production needs. Custom middleware is for app-specific concerns (auth checks, custom logging, domain budgets).

---

## Slide 11: The production middleware stack

Copy-paste-ready default. Order matters.

```python
middleware=[
    # Cost containment FIRST (so retries can't blow the budget)
    ModelCallLimitMiddleware(run_limit=50),
    ToolCallLimitMiddleware(run_limit=200),

    # Resilience to transient failures
    ModelRetryMiddleware(max_retries=3, backoff_factor=2.0),
    ToolRetryMiddleware(max_retries=3, backoff_factor=2.0),

    # Provider-level resilience
    ModelFallbackMiddleware("openai:gpt-4o-mini"),

    # Long-conversation hygiene
    SummarizationMiddleware(model="claude-haiku-4-5",
                            trigger=("tokens", 8000),
                            keep=("messages", 20)),

    # Privacy (only if input may contain PII)
    PIIMiddleware("email", strategy="redact", apply_to_input=True),
]
```

Add `HumanInTheLoopMiddleware` for any tool that touches money / external messaging / irreversible state. **Requires a checkpointer.**

> Speaker notes: ordering rationale: limits before retries means retries can't multiply your budget. Privacy redaction before logging. Summarization runs before model call, not after.

---

## Slide 12: Productionisation — durable execution

A graph is "durable" iff it has a checkpointer at compile time.

```python
from langgraph.checkpoint.postgres import PostgresSaver

agent = create_agent(
    model="...", tools=[...], middleware=[...],
    checkpointer=PostgresSaver.from_conn_string(POSTGRES_URL),
)

# Every invocation must pass thread_id
result = agent.invoke(
    {"messages": [...]},
    config={"configurable": {"thread_id": f"user-{uid}-conv-{cid}"}},
)
```

| Checkpointer | When |
|---|---|
| `InMemorySaver` | Dev only |
| `SqliteSaver` | Single-node low-volume |
| `PostgresSaver` | **Production** — multi-instance safe |

Resume an interrupted thread: `agent.invoke(None, config={...same thread_id...})`.

> Speaker notes: HITL middleware needs a checkpointer or interrupts crash. Cleanup of old checkpoint rows is the user's job — set a TTL job or app-layer expiration.

---

## Slide 13: Three deploy targets

| Target | When | Tool |
|---|---|---|
| **LangSmith Cloud** | Managed, lowest ops | `langgraph build/deploy` |
| **Google Cloud Run** | GCP shop, serverless container | `gcloud run deploy --source` |
| **Docker** | Self-host, full control | `docker build/run` |

All three gated on **smoke pre-flight** (`python evals/run.py --smoke`). Recommended pattern, not enforced.

> Speaker notes: chose to leave the smoke gate as a recommendation rather than CLI-enforced (which v1's Python CLI did) because we no longer ship a CLI. The deploy skill teaches the agent to do this manually.

---

## Slide 14: Cloud Run — the integrated recipe

```bash
# 1. Smoke pre-flight
python evals/run.py --smoke

# 2. Sync .env → Secret Manager (one secret per key)
#    Naming: <service>-<lowercase-key-with-hyphens>
#    Example: OPENAI_API_KEY → my-agent-openai-api-key

# 3. Deploy IAM-gated by default
gcloud run deploy my-agent \
  --source . \
  --no-allow-unauthenticated \
  --set-secrets "OPENAI_API_KEY=my-agent-openai-api-key:latest,..." \
  --quiet

# 4. Verify
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" "$URL/healthz"
```

`--source .` lets Cloud Build do image build + Artifact Registry push. We don't manage AR repos ourselves.

> Speaker notes: defaults: IAM-gated (private) and Secret Manager. Both are GCP-recommended for production. Public is one flag away (--allow-unauthenticated). Plain --set-env-vars exposes secrets in `gcloud run services describe` output as plaintext — bad.

---

## Slide 15: Cloud Run state — Postgres

Cloud Run instances are stateless and can be killed at any moment.

- `InMemorySaver` loses conversation state on every cold start.
- **Use `PostgresSaver` pointed at Cloud SQL.** Connect via Cloud SQL Auth Proxy or Unix socket: `/cloudsql/<project>:<region>:<instance>`.
- The FastAPI host (`server/app.py`) accepts a `thread_id` parameter on every request and passes it through to `agent.invoke(..., config={"configurable": {"thread_id": ...}})`.

Without `thread_id` passthrough, every request is a fresh thread — durable execution and HITL break.

> Speaker notes: this integration (Cloud Run + Cloud SQL + FastAPI thread_id passthrough) is NOT in any single LangChain doc page. The deploy skill is the only place this recipe lives as a coherent whole.

---

## Slide 16: DeepAgents in production

`create_deep_agent` = `create_agent` + 3 pre-installed middlewares.

**Filesystem backend choice:**
| Backend | Scope |
|---|---|
| Default in-memory | Single invocation (dev) |
| `StateBackend` | Single thread |
| `StoreBackend(namespace=(asst_id, user_id))` | **Per-user persistent (production default)** |
| `CompositeBackend` | Mix |

**Sandboxed tools (Daytona):** thread-scoped or assistant-scoped. **Critical:** never pass raw API keys into the sandbox — use the auth proxy.

**Stack the production middlewares on top via `middleware=[...]`** in `create_deep_agent` — adds, doesn't replace.

> Speaker notes: per-user namespace prevents cross-user file leakage. The naming convention is from the LangChain docs.

---

## Slide 17: Eval + testing — three layers

1. **Unit tests** (no API calls) — `LLMToolEmulator` middleware fakes tool execution; `FakeChatModel` for the model.
2. **Integration tests** — real model, real middleware, hermetic tools. `pytest -m integration`.
3. **Trajectory + dataset tests** via `langsmith` pytest plugin — each test uploads to LangSmith, runs evaluators, fails on score threshold.

```python
@t.expect(score_min=0.8, evaluator="correctness")
@pytest.mark.parametrize("example", [...])
def test_basic_qa(example):
    return agent.invoke({"messages": example["messages"]})
```

**Eval-as-monitor in production:** the same evaluators run continuously against live traces; alert when score drops.

> Speaker notes: smoke evals (3-5 rows, <60s) run pre-deploy. Full eval suite runs async post-deploy or on PR. Production eval-as-monitor catches model drift / prompt rot.

---

## Slide 18: Observability

Tracing turns on automatically when `LANGSMITH_TRACING=true`. No code changes.

- Every `agent.invoke(...)` is one trace.
- Tool calls, sub-agent delegations, middleware hooks → nested spans.
- `@traceable` decorator for application-specific spans (DB queries, etc.).

**OpenTelemetry integration:** `LANGSMITH_OTEL_ENABLED=true` dual-emits to LangSmith + your OTLP collector (Honeycomb, Datadog, Tempo).

**Distributed tracing:** propagate context with `propagate.inject(headers)` for cross-service calls.

**Sampling for high traffic:** `LANGSMITH_SAMPLING_RATE=0.1` — full trace integrity preserved on sampled traces.

> Speaker notes: the observability skill ships a 12-row failure-mode lookup table mapping symptoms to first-thing-to-check. Coding agents reach for it when something's wrong.

---

## Slide 19: Repo structure (post-pivot)

```
agent_cli_langchain/
├── README.md          # install both: skills + mcpdoc
├── CONTRIBUTING.md    # how to propose / edit skills
├── LICENSE            # Apache-2.0
├── .gitignore
└── skills/            # the deliverable — 9 .md files
    ├── langchain-agents-workflow.md
    ├── langchain-agents-scaffold.md
    ├── langchain-agents-middleware.md
    ├── langchain-agents-langgraph-code.md
    ├── langchain-agents-deepagents-code.md
    ├── langchain-agents-langchain-code.md
    ├── langchain-agents-langsmith-evals.md
    ├── langchain-agents-deploy.md
    └── langchain-agents-observability.md
```

Branch: `main`. Tag `v1-implementation-archive` preserves the deleted Python implementation (recoverable).

> Speaker notes: ~1300 lines of skill content + ~120 line README + LICENSE + CONTRIBUTING. That's the entire shipped surface area.

---

## Slide 20: Install

**1. Skill bundle:**

```bash
npx skills add cwijayasundara/agent_cli_langchain
```

**2. `mcpdoc` MCP server (required companion):**

```bash
claude mcp add-json langchain-docs '{
  "command": "uvx",
  "args": ["--from", "mcpdoc", "mcpdoc",
           "--urls", "LangChain:https://docs.langchain.com/llms.txt",
           "--transport", "stdio"]
}'
```

Verify:

```bash
claude mcp list   # should show: langchain-docs - ✓ Connected
```

`--urls` syntax is **strict** — single string, space-separated `Name:URL` pairs. Not multiple args.

> Speaker notes: the strict `--urls` syntax was a footgun in v1 of the README — fixed in commit 4b92639. uvx ships with uv; pipx run mcpdoc works too.

---

## Slide 21: Runtime model

How a coding agent uses the bundle + mcpdoc together at invocation time:

1. User asks: *"Add a sub-agent to my DeepAgent that does web search."*
2. Agent loads `langchain-agents-deepagents-code` skill (description trigger matches).
3. Skill says: *"Sub-agents go in `SUBAGENTS = [...]`. For exact API, fetch `https://docs.langchain.com/oss/python/deepagents/...`"*.
4. Agent calls `mcpdoc.fetch_docs(url)` — gets live API reference.
5. Agent combines editorial guidance + live API to write the code.

Without `mcpdoc`, agents fall back to training-data memory of the API — which drifts.

> Speaker notes: this is the design centerpiece. Skills tell the agent how to think; mcpdoc tells the agent what the API actually is. Together they form a complete coding-agent assist.

---

## Slide 22: Maintenance strategy

**The bundle ages slowly because we trimmed API reference out.**

- API drifts → mcpdoc handles it (zero work for us).
- Editorial content (production stack, ordering rationale, gotchas) stable across versions.
- Estimated maintenance burden: ~50% lower vs. v1 (which embedded API examples).

**What CAN drift:**
- Middleware names (LangChain renames)
- Recommended model names (`claude-sonnet-4-6` ages)
- LangSmith API conventions

**Mitigation:** scheduled refresh review every ~6 weeks (one LangChain release cycle).

> Speaker notes: the v1 design (Python CLI) had hard-coded version pins, scaffold templates that mirrored framework APIs, etc. — high maintenance. The skill bundle inherits much less of that surface.

---

## Slide 23: What we explicitly didn't build

Per spec §3 of the pivot doc, no longer in scope:

- A Python CLI binary (was v1; pivoted away).
- A canonical scaffolded project layout (each official tool has its own).
- Skill installation tooling beyond `npx skills add`.
- Cursor / Gemini CLI / Antigravity skill installers (skill files work in those agents directly).
- Cloud Run / Lambda / K8s as discrete CLI commands (recipes in skills only).
- RAG ingestion pipelines (LangChain has its own loader story).
- TUI / REPL.
- Multi-project monorepo support.

> Speaker notes: each explicit non-goal is one less thing to maintain. The bundle's value is the editorial content; everything else is a distraction.

---

## Slide 24: Design history

| Phase | What | Outcome |
|---|---|---|
| Brainstorm | Defined positioning, scope, deploy targets | Spec approved |
| v1 plan | 20-task implementation of Python CLI + skills | Plan approved |
| v1 build | 22 commits via subagent-driven development | All tests green |
| Pivot | Realised agents-cli's public repo is itself skills-only | One mass-delete commit |
| mcpdoc reorientation | Trimmed three code skills; doc-server companion | -25% bundle lines |
| Productionisation pass | Added middleware skill; production stack | +1 skill |
| README / install fixes | Fixed `--urls` syntax bug; expanded with troubleshooting | — |
| `master → main` | Renamed default branch | — |

All preserved in git history. Tag `v1-implementation-archive` recoverable.

> Speaker notes: the pivot was the biggest course correction. Hard but right call. ~70% of v1's deleted code; 5% of value lost.

---

## Slide 25: Future work (candidates, not committed)

- **Skill drift checker** — scheduled CI job that fetches `mcpdoc` URLs the skills point at; flags 404s and broken examples.
- **Per-IDE install instructions** — Cursor / Windsurf / Claude Desktop config snippets in the README beyond a pointer.
- **DeepAgents-specific `llms.txt`** — if upstream ships one, register it alongside the LangChain one.
- **Eval skill expansion** — add a section on eval-driven prompt iteration (current skill is light here).
- **`langchain-agents-security`** — new skill on prompt injection, tool-call validation, sandbox escape patterns. Currently scattered across deepagents-code and deploy.

Open questions:
- Should the bundle ship its own `llms.txt`? (Probably no — single skill bundle, not a docs site.)
- A skill marketplace listing? (Wait for the ecosystem to settle.)

> Speaker notes: nothing committed. Roadmap captured here for reference.

---

## Slide 26: Q&A

- **Q: Why not just use mcpdoc by itself?**
  A: Docs are reference, not opinion. Without skills, agents miss the production middleware stack, default to public Cloud Run, bake `.env` into images.

- **Q: Why not just use skills by itself?**
  A: API reference content rots with every release. mcpdoc keeps it fresh for free.

- **Q: Why Apache-2.0?**
  A: Ecosystem standard. Permissive enough for proprietary use; gives patent grant. Same as LangChain itself.

- **Q: How do you keep this in sync with LangChain v2/v3?**
  A: Editorial content stable. mcpdoc handles API drift. Scheduled review every ~6 weeks per release cycle.

> Speaker notes: most predictable questions. If audience is engineering, the maintenance one is the one that matters most.

---

## Slide 27: Repo + contact

- **Repo:** https://github.com/cwijayasundara/agent_cli_langchain
- **Default branch:** `main`
- **Latest commit:** see `git log`
- **Tag:** `v1-implementation-archive` (deleted Python CLI; recoverable)
- **License:** Apache-2.0
- **Contributions:** see `CONTRIBUTING.md` — skill edits + new skills welcome.

Built with Claude Code (Opus 4.7, 1M context) over a single working session, via the superpowers:brainstorming → writing-plans → subagent-driven-development workflow.

> Speaker notes: the design + brainstorm + plan + execution were all in one session. The skill bundle itself is also a product OF this kind of skill-driven workflow.
