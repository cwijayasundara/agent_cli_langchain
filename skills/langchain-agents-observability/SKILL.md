---
name: langchain-agents-observability
description: Use when debugging an agent's behaviour, reading LangSmith traces, setting up tracing in production (LangSmith + OpenTelemetry), wiring distributed tracing across services, or diagnosing common failure modes.
---

# Observability

LangChain ecosystem projects trace through **LangSmith** by default. Tracing turns on automatically when `LANGSMITH_TRACING=true` is set — no code changes required. Every `agent.invoke(...)` becomes one trace; tool calls, sub-agent delegations, and middleware hooks are nested spans.

For production, you'll often want OTEL on top of (or instead of) LangSmith.

## Required environment variables

```
LANGSMITH_API_KEY=ls_...        # required
LANGSMITH_TRACING=true          # enables capture
LANGSMITH_PROJECT=my-agent      # bucket name in the LangSmith UI
```

If `LANGSMITH_TRACING` is unset or `false`, the agent runs but no traces are captured. The agent does *not* fail — silent observability gap. Always set it explicitly.

## Where traces live

LangSmith UI → the project named in `LANGSMITH_PROJECT`. Filter by experiment, time range, or status. Each trace is a tree:
- Top-level: `agent.invoke(...)`.
- Children: middleware `wrap_*` calls, model calls, tool calls, sub-agent `task` invocations.
- Leaves: token streams, tool inputs/outputs, errors with stack traces.

## What middleware looks like in traces

Each middleware that wraps a model or tool call appears as its own span. Useful for diagnosing "why did this take so long" — you can see exactly which retry or fallback fired.

## Manual span instrumentation

```python
from langsmith import traceable

@traceable
def my_helper(x: int) -> int:
    return x * 2
```

`@traceable` works on any callable; it shows up as its own span under the parent trace. Use it for application-specific operations not auto-captured (DB queries, external API calls outside of LangChain tools).

## OpenTelemetry integration

LangSmith can emit OTLP traces alongside its native ones, so existing observability backends (Jaeger, Tempo, Honeycomb, Datadog) get the data:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://api.honeycomb.io"
export OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=$HONEYCOMB_API_KEY"
export LANGSMITH_OTEL_ENABLED=true
```

When `LANGSMITH_OTEL_ENABLED=true`, traces are dual-emitted: to LangSmith AND to your OTLP collector. Spans use OpenTelemetry semantic conventions for AI / LLM workflows.

## Distributed tracing across services

If your agent calls another service (e.g. a separate retriever microservice), propagate the trace context so spans link up:

```python
from opentelemetry import propagate, trace

# When making an outbound call:
headers = {}
propagate.inject(headers)   # adds traceparent header
requests.post("https://retriever.internal/", headers=headers, json={...})
```

The downstream service should call `propagate.extract(request.headers)` and create a span as a child.

## Cloud Run-specific tracing

Cloud Run automatically adds `X-Cloud-Trace-Context` to incoming requests. To correlate Cloud Run access logs with LangSmith spans, log the trace ID at the start of each request handler:

```python
import os, structlog
log = structlog.get_logger()

@app.post("/invoke")
def invoke(req, request: Request):
    trace_header = request.headers.get("X-Cloud-Trace-Context", "")
    cloud_trace_id = trace_header.split("/")[0]
    log.bind(cloud_trace_id=cloud_trace_id, thread_id=req.thread_id).info("invoke")
    ...
```

## Common failure-mode diagnostics

| Symptom | Likely cause | First thing to check |
|---|---|---|
| `agent` import fails | Missing dep, wrong path, syntax error | `python -c "from agent.agent import agent"` from project root |
| Smoke evals fail with auth error | Wrong / missing provider key | `python -c "import os; print(bool(os.getenv('OPENAI_API_KEY')))"` |
| Smoke evals fail with rate-limit | Provider rate limit during eval | Drop dataset to 1 row; add `ModelRetryMiddleware`; retry |
| `langgraph dev` hangs on start | `langgraph.json` graph path wrong | `cat langgraph.json` — verify `./agent/agent.py:agent` exists |
| `langgraph dev` reload stops | Latest edit broke import | Check terminal for the exception |
| Docker container crashes on boot | `.env` not passed at run time | `docker logs <container>` |
| Cloud Run service doesn't start | Listening on 127.0.0.1 instead of 0.0.0.0:$PORT | `gcloud run services logs read SERVICE` |
| Trace shows the LLM but no tool calls | Tool not registered with the model | `bind_tools(TOOLS)` (LangGraph) or `tools=...` arg to `create_agent` |
| Trace shows tool calls but they fail | Tool raised an exception | Click the failing span — exception + traceback are captured |
| Conversation memory lost between turns | No checkpointer or thread_id mismatch | `compile(checkpointer=...)` AND `config={"configurable": {"thread_id": ...}}` on every invoke |
| Token cost suddenly spikes | No `SummarizationMiddleware`; long context | Add it; trigger at ~8000 tokens, keep last 20 messages |
| Random 30-60s pauses in production | Provider rate-limit handled by retry middleware | Check trace — `ModelRetryMiddleware` span shows the backoff sleeps |
| HITL `interrupt()` never resumes | No checkpointer at compile time | `HumanInTheLoopMiddleware` requires a checkpointer |
| Costs much higher than expected | Retries multiplying. No `ModelCallLimitMiddleware` | Add it; cap at e.g. `run_limit=50` |

## Quick local verification (no LangSmith needed)

```bash
python -c "
from agent.agent import agent
result = agent.invoke({'messages': [{'role': 'user', 'content': 'hello'}]})
print(result)
"
```

If this fails, the agent is broken regardless of tracing. Fix it first.

## Production alerting

LangSmith UI supports alerts on:
- p95 latency exceeding a threshold.
- Error rate exceeding a threshold (% of runs that throw).
- Specific evaluator scores dropping below a threshold (eval-as-monitor pattern).

Configure these per project in the LangSmith UI. For escalation to PagerDuty / Slack, use LangSmith's webhook integrations or pipe traces through OTEL into your existing alert stack.

## Trace sampling for high-volume services

LangSmith captures every trace by default. For very high traffic (>100 RPS sustained), sampling is supported via the `LANGSMITH_SAMPLING_RATE` env var (e.g. `0.1` = 10%). Trace integrity is preserved for sampled traces (full tree), so this is safe — you just see fewer of them.

## Trace URLs in code

When `LANGSMITH_TRACING=true`, the SDK prints a trace URL to stderr after each `agent.invoke(...)`. Capture it in production logs for debugging:

```python
import sys, contextlib, io

buf = io.StringIO()
with contextlib.redirect_stderr(buf):
    result = agent.invoke({"messages": [...]})
trace_url = next((line for line in buf.getvalue().splitlines() if "smith.langchain.com" in line), "")
log.info("agent_invoked", trace_url=trace_url)
```
