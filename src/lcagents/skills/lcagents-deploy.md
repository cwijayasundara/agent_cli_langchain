---
name: lcagents-deploy
description: Use when preparing or executing a deploy — setting secrets, picking targets, smoke-testing.
---

# lcagents Deploy

## Targets

- `lcagents deploy langsmith` — pushes via `langgraph build/deploy` to LangSmith Cloud.
- `lcagents deploy docker --tag <name:tag>` — builds a self-contained image; optional `--push <registry>`.

Both run a smoke pre-flight. If smoke fails, **fix the agent or the smoke dataset; do not bypass**.

## Secrets

- `.env` is the source of truth; populated by `lcagents login`.
- LangSmith deploy pushes secrets to LangSmith via API.
- Docker deploy does **not** bake secrets into the image. The CLI prints the `docker run --env-file .env` invocation.
- **Never** print or display `.env` content.

## After deploy

LangSmith: open the printed trace URL.
Docker: `docker run --env-file .env -p 8080:8080 <tag>` then `curl localhost:8080/healthz`.
