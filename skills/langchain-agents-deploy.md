---
name: langchain-agents-deploy
description: Use when deploying a LangChain / LangGraph / DeepAgents project. Covers LangSmith Cloud, Google Cloud Run, and self-hosted Docker — three self-contained recipes with secrets handling and pre-flight smoke testing.
---

# Deploy

Three deploy targets. Pick based on the user's preference:

| Target | When to pick | Tool |
|---|---|---|
| **LangSmith Cloud** | Managed, simplest, lowest ops burden | `langgraph build/deploy` |
| **Google Cloud Run** | GCP shop, want a managed serverless container | `gcloud run deploy --source` |
| **Docker** | Self-host anywhere, full control | `docker build` + `docker run` |

## Pre-flight: smoke test (recommended for all targets)

Before any deploy, run the user's smoke evalset. This is not enforced; you must do it.

```bash
LANGSMITH_API_KEY=... python evals/run.py --smoke
```

If smoke fails, **fix the agent or the smoke dataset; do not bypass**. See the `langchain-agents-langsmith-evals` skill.

## Never print secrets

Both Cloud Run (Secret Manager) and Docker (`--env-file`) avoid baking secrets into deployable artifacts. Refer to keys by name only — never print, cat, or log `.env` contents.

---

## Target 1: LangSmith Cloud

Requires `LANGSMITH_API_KEY` and a `langgraph.json` in the project root.

```bash
# 1. Smoke pre-flight
LANGSMITH_API_KEY=$LANGSMITH_API_KEY python evals/run.py --smoke

# 2. Build
langgraph build -t my-agent

# 3. Deploy
langgraph deploy
```

`langgraph deploy` pushes the build to LangSmith Cloud and returns the deployment URL. Print that URL prominently to the user.

For secret management, set them in the LangSmith UI under the deployment's settings, or via `langgraph deploy --env KEY=value` (one flag per secret — the LangSmith CLI handles secure storage).

---

## Target 2: Google Cloud Run

Uses `gcloud run deploy --source .` so Cloud Build does the image build and Artifact Registry push. No need to manage AR repos or push images yourself.

### Prerequisites (verify before deploying)

```bash
# 1. gcloud installed and authenticated
gcloud auth list --filter=status:ACTIVE --format="value(account)"   # must return at least one account

# 2. Project + region set (check, don't assume)
gcloud config get-value project
gcloud config get-value compute/region

# 3. Required APIs enabled (deploy will fail with cryptic errors if not)
gcloud services list --enabled --filter="config.name:(run.googleapis.com OR cloudbuild.googleapis.com OR secretmanager.googleapis.com)" --format="value(config.name)"
```

If any API is missing, enable it (and tell the user you're doing so):

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

### Project must contain a Dockerfile or Cloud Build will use Buildpacks

Cloud Build will autodetect a `Dockerfile` if present. For LangChain projects, a multi-stage `server/Dockerfile` is the standard shape — see the **Docker** target below for the recipe. Place the Dockerfile at the repo root (or pass `--dockerfile path` to override).

The container must listen on the port from `$PORT` (Cloud Run sets this — defaults to 8080).

### Sync secrets to Secret Manager

For each `KEY=value` in `.env`, create or update a Secret Manager secret. Naming convention: `<service>-<lowercase-key-with-hyphens>`. So `OPENAI_API_KEY` becomes `my-agent-openai-api-key`.

```bash
SERVICE=my-agent
while IFS='=' read -r key value; do
  # skip comments and blank lines
  [[ -z "$key" || "$key" =~ ^# ]] && continue
  secret_name="${SERVICE}-$(echo "$key" | tr '[:upper:]_' '[:lower:]-')"

  if gcloud secrets describe "$secret_name" >/dev/null 2>&1; then
    echo "$value" | gcloud secrets versions add "$secret_name" --data-file=-
  else
    echo "$value" | gcloud secrets create "$secret_name" --data-file=- --replication-policy=automatic
  fi
done < .env
```

### Deploy

IAM-gated by default. The user must opt in to public via `--allow-unauthenticated`. Build the `--set-secrets` flag from the secrets you synced above.

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

For a public demo URL, swap `--no-allow-unauthenticated` for `--allow-unauthenticated`. Default to private — public is one flag away when you actually want it.

### Verify the deploy

```bash
URL=$(gcloud run services describe "$SERVICE" --region us-central1 --format="value(status.url)")

# IAM-gated default:
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" "$URL/healthz"

# Or if --allow-unauthenticated:
curl "$URL/healthz"
```

Expect a `200 {"ok": true}`. Print the URL prominently.

### Common Cloud Run failure modes

| Symptom | Cause |
|---|---|
| `Service did not start within the allocated time` | Container takes >4 min cold-start. Heavy `pip install` in startup → bake everything into the image instead. |
| `PORT not listened on` | App is bound to 127.0.0.1 or wrong port. Listen on `0.0.0.0:$PORT`. |
| `Permission denied` on secrets | The Cloud Run service account needs `roles/secretmanager.secretAccessor`. Grant via `gcloud projects add-iam-policy-binding`. |
| 403 on `--no-allow-unauthenticated` | Caller missing `roles/run.invoker`. Grant or pass an identity token. |

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
"""Tiny FastAPI host. POST /invoke {"input": {"messages": [...]}}"""
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


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.post("/invoke")
def invoke(req: InvokeRequest) -> dict:
    return {"output": agent.invoke(req.input)}


@app.post("/stream")
async def stream(req: InvokeRequest) -> StreamingResponse:
    async def gen() -> AsyncGenerator[bytes, None]:
        async for chunk in agent.astream(req.input):
            yield (json.dumps(chunk, default=str) + "\n").encode("utf-8")
    return StreamingResponse(gen(), media_type="application/x-ndjson")
```

### Build & run

```bash
# 1. Smoke pre-flight
python evals/run.py --smoke

# 2. Build
docker build -f server/Dockerfile -t my-agent:latest .

# 3. Smoke-test the container locally before pushing anywhere
docker run --rm -d --name agent-test --env-file .env -p 8080:8080 my-agent:latest
sleep 2
curl -s -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "hello"}]}}'
docker stop agent-test

# 4. Run for real
docker run -d --name my-agent --env-file .env -p 8080:8080 my-agent:latest
```

**Never bake `.env` into the image.** Always pass `--env-file .env` (or individual `-e KEY=...` flags) at run time. The Dockerfile above does not `COPY .env` for this reason.

For pushing to a registry: `docker tag my-agent:latest registry/my-agent:latest && docker push registry/my-agent:latest`.
