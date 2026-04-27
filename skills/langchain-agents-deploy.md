---
name: langchain-agents-deploy
description: Use when productionising or deploying a LangChain / LangGraph / DeepAgents agent. Covers durable execution (checkpointers, thread_id), the production middleware stack, three deploy targets (LangSmith Cloud, Cloud Run, Docker), secrets, scaling, and post-deploy verification.
---

# Deploy + Productionisation

This skill has two halves: **productionisation** (what to put in the agent BEFORE you deploy it anywhere) and **deploy** (how to ship it).

---

# Part 1: Productionisation

A "production-ready" agent has three things any toy agent does not:

1. **Durable execution** — a checkpointer + thread_id so state survives restarts and `interrupt()` works.
2. **The production middleware stack** — call limits, retries, fallbacks, summarization, PII handling, optional HITL.
3. **Smoke evals you actually run before each deploy.**

## Durable execution

A graph becomes durable by attaching a checkpointer at compile time. Without one, `interrupt()` and `HumanInTheLoopMiddleware` do nothing useful, and crash recovery is impossible.

```python
from langgraph.checkpoint.postgres import PostgresSaver

agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[...],
    middleware=[...],            # see below
    checkpointer=PostgresSaver.from_conn_string("postgresql://..."),
)
```

| Checkpointer | When |
|---|---|
| `InMemorySaver` | Dev, tests, smoke runs. State dies with the process. |
| `SqliteSaver` | Single-node deploys, low-volume. |
| `PostgresSaver` | Multi-instance, production. Concurrent threads safe. |

Every invocation must pass a `thread_id`:

```python
result = agent.invoke(
    {"messages": [...]},
    config={"configurable": {"thread_id": f"user-{user_id}-conv-{conv_id}"}},
)
```

To resume an interrupted thread (HITL approval, crash recovery), pass `None` as the input with the same `thread_id`:

```python
result = agent.invoke(None, config={"configurable": {"thread_id": "user-42-conv-7"}})
```

**Cleanup:** old checkpoints accumulate. Either set up a job that deletes rows older than N days from the checkpoint table, or run with a TTL strategy at the app layer (drop threads older than X). The LangChain docs do not ship a built-in cleaner; this is your job.

## The production middleware stack

Copy this and tune. See the `langchain-agents-middleware` skill for full details on each.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware, ToolCallLimitMiddleware,
    ModelRetryMiddleware, ToolRetryMiddleware,
    ModelFallbackMiddleware, SummarizationMiddleware,
    HumanInTheLoopMiddleware, PIIMiddleware,
)
from langgraph.checkpoint.postgres import PostgresSaver

agent = create_agent(
    model="claude-sonnet-4-6",
    tools=TOOLS,
    middleware=[
        # Order matters: limits BEFORE retries (so retries can't blow the budget)
        ModelCallLimitMiddleware(run_limit=50),
        ToolCallLimitMiddleware(run_limit=200),

        # Resilience to transient failures
        ModelRetryMiddleware(max_retries=3, backoff_factor=2.0),
        ToolRetryMiddleware(max_retries=3, backoff_factor=2.0),

        # Provider-level resilience
        ModelFallbackMiddleware("openai:gpt-4o-mini"),

        # Long-conversation hygiene
        SummarizationMiddleware(model="claude-haiku-4-5", trigger=("tokens", 8000), keep=("messages", 20)),

        # HITL on irreversible tools (requires checkpointer; below)
        HumanInTheLoopMiddleware(interrupt_on={
            "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
            "charge_card": {"allowed_decisions": ["approve", "reject"]},
        }),

        # Privacy (only if input may contain PII)
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
    ],
    checkpointer=PostgresSaver.from_conn_string(os.environ["POSTGRES_URL"]),
)
```

## Cost controls beyond `ModelCallLimitMiddleware`

- **Pick a small fallback.** `ModelFallbackMiddleware("openai:gpt-4o-mini")` after a strong primary keeps costs bounded on retries.
- **Use `LLMToolSelectorMiddleware`** when the agent has 10+ tools. A small model picks the relevant 3–5 to expose to the main model, dropping prompt tokens.
- **Use `SummarizationMiddleware`** on long conversations. Summarize every N tokens to keep prompt size bounded.
- **Use `ContextEditingMiddleware`** to drop old tool outputs from context once they're no longer useful.

## Structured outputs

If the agent's final answer must be typed (an extracted record, a decision), use `model.with_structured_output(...)` *as the model passed to `create_agent`*:

```python
from pydantic import BaseModel

class Decision(BaseModel):
    action: str
    confidence: float

structured_model = init_chat_model("claude-sonnet-4-6").with_structured_output(Decision)

agent = create_agent(model=structured_model, tools=[...], middleware=[...])
```

The agent's terminal AIMessage will be a validated `Decision` instance.

## Smoke pre-flight (recommended before every deploy)

Keep `evals/datasets/smoke.jsonl` to 3–5 rows, <60s total. Run before every deploy:

```bash
LANGSMITH_API_KEY=... python evals/run.py --smoke
```

If smoke fails, **fix the agent or the smoke dataset; do not bypass.** See the `langchain-agents-langsmith-evals` skill for the runner shape.

## Never print secrets

Refer to keys by name only — never print, cat, or log `.env` contents. This holds for ALL deploy targets.

---

# Part 2: Deploy targets

Three options. Pick by user preference:

| Target | When | Tool |
|---|---|---|
| **LangSmith Cloud** | Managed, simplest, lowest ops burden, durable execution baked in | `langgraph build/deploy` |
| **Google Cloud Run** | GCP shop, want managed serverless container | `gcloud run deploy --source` |
| **Docker** | Self-host anywhere, full control | `docker build` + `docker run` |

## Target 1: LangSmith Cloud

Requires `LANGSMITH_API_KEY` and `langgraph.json` in the project root.

```bash
# Smoke pre-flight
python evals/run.py --smoke

# Build + deploy
langgraph build -t my-agent
langgraph deploy
```

`langgraph deploy` pushes to LangSmith Cloud (managed Agent Server) and prints the deployment URL. State persistence and durable execution are managed for you — you don't need to set up Postgres yourself; LangSmith provides it.

For secrets: set them in the LangSmith UI under the deployment's settings, or `langgraph deploy --env KEY=value` (one flag per secret — securely stored).

For scaling: LangSmith handles horizontal scaling; you configure concurrency / min-instances in the UI.

---

## Target 2: Google Cloud Run

`gcloud run deploy --source .` does it all: Cloud Build builds the image (using the project's Dockerfile if present), pushes to Artifact Registry, deploys the service. No local Docker needed.

### Prerequisites

```bash
# Authenticated
gcloud auth list --filter=status:ACTIVE --format="value(account)"

# Project + region
gcloud config get-value project
gcloud config get-value compute/region

# Required APIs
gcloud services list --enabled --filter="config.name:(run.googleapis.com OR cloudbuild.googleapis.com OR secretmanager.googleapis.com)" --format="value(config.name)"
```

If APIs missing:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

### Sync secrets to Secret Manager

For each `KEY=value` in `.env`, ensure a Secret Manager secret exists. Naming: `<service>-<lowercase-key-with-hyphens>`. So `OPENAI_API_KEY` → `my-agent-openai-api-key`.

```bash
SERVICE=my-agent
while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" =~ ^# ]] && continue
  secret_name="${SERVICE}-$(echo "$key" | tr '[:upper:]_' '[:lower:]-')"
  if gcloud secrets describe "$secret_name" >/dev/null 2>&1; then
    echo "$value" | gcloud secrets versions add "$secret_name" --data-file=-
  else
    echo "$value" | gcloud secrets create "$secret_name" --data-file=- --replication-policy=automatic
  fi
done < .env
```

### Deploy (IAM-gated by default)

```bash
SECRETS_FLAG=$(while IFS='=' read -r key _; do
  [[ -z "$key" || "$key" =~ ^# ]] && continue
  secret_name="${SERVICE}-$(echo "$key" | tr '[:upper:]_' '[:lower:]-')"
  echo -n "${key}=${secret_name}:latest,"
done < .env | sed 's/,$//')

gcloud run deploy "$SERVICE" \
  --source . \
  --region us-central1 \
  --port 8080 \
  --no-allow-unauthenticated \
  --set-secrets "$SECRETS_FLAG" \
  --quiet
```

For a public demo URL, swap `--no-allow-unauthenticated` for `--allow-unauthenticated`. Default to private; public is one flag away.

### Post-deploy verification

```bash
URL=$(gcloud run services describe "$SERVICE" --region us-central1 --format="value(status.url)")
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" "$URL/healthz"
```

### Common Cloud Run failure modes

| Symptom | Cause |
|---|---|
| `Service did not start within the allocated time` | Container takes >4min cold-start. Heavy `pip install` in startup → bake everything into the image. |
| `PORT not listened on` | App is bound to 127.0.0.1 or wrong port. Listen on `0.0.0.0:$PORT`. |
| `Permission denied` on secrets | Service account needs `roles/secretmanager.secretAccessor`. |
| 403 on `--no-allow-unauthenticated` | Caller missing `roles/run.invoker`. |
| Lost state between requests | Cloud Run is stateless. Use `PostgresSaver` (managed Cloud SQL) for the checkpointer; in-process state will be lost. |

### State on Cloud Run

Cloud Run instances are stateless and can be killed at any moment. **Use a `PostgresSaver` checkpointer pointed at Cloud SQL.** `InMemorySaver` will lose conversation state on every cold start. Connect via the Cloud SQL Auth Proxy or a Unix socket (`/cloudsql/<project>:<region>:<instance>`).

---

## Target 3: Docker (self-hosted)

### Multi-stage Dockerfile (place at `server/Dockerfile`)

```dockerfile
# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev
COPY agent/ ./agent/
COPY server/ ./server/

FROM python:3.11-slim AS runtime
RUN useradd -m -u 1000 app
WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8080
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### FastAPI host (`server/app.py`)

```python
from __future__ import annotations
import json
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()
from agent.agent import agent  # noqa: E402

app = FastAPI()


class InvokeRequest(BaseModel):
    input: dict
    thread_id: str | None = None


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.post("/invoke")
def invoke(req: InvokeRequest) -> dict:
    config = {"configurable": {"thread_id": req.thread_id}} if req.thread_id else {}
    return {"output": agent.invoke(req.input, config)}


@app.post("/stream")
async def stream(req: InvokeRequest) -> StreamingResponse:
    config = {"configurable": {"thread_id": req.thread_id}} if req.thread_id else {}
    async def gen() -> AsyncGenerator[bytes, None]:
        async for chunk in agent.astream(req.input, config):
            yield (json.dumps(chunk, default=str) + "\n").encode("utf-8")
    return StreamingResponse(gen(), media_type="application/x-ndjson")
```

The `thread_id` parameter is what makes the deploy compatible with durable execution and HITL — without passing it through, every request starts a fresh thread.

### Build & run

```bash
# Smoke pre-flight
python evals/run.py --smoke

# Build
docker build -f server/Dockerfile -t my-agent:latest .

# Local smoke-test
docker run --rm -d --name agent-test --env-file .env -p 8080:8080 my-agent:latest
sleep 2
curl -s -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "hello"}]}, "thread_id": "test-1"}'
docker stop agent-test

# Run for real
docker run -d --name my-agent --env-file .env -p 8080:8080 my-agent:latest
```

**Never bake `.env` into the image.** Always pass `--env-file` at run time. The Dockerfile above does not `COPY .env` for this reason.

For state: point `PostgresSaver` at an external Postgres (RDS, Cloud SQL, etc.). Don't run Postgres inside the same container.

### Scaling self-hosted

- Run multiple instances behind a load balancer. With `PostgresSaver`, threads are correctly serialized across instances by `thread_id`.
- Concurrency per instance: tune `uvicorn --workers N --worker-class uvicorn.workers.UvicornWorker`.
- For very long-running threads, configure your LB's idle timeout above your max expected agent runtime.
