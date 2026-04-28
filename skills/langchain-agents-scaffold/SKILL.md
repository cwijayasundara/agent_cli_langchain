---
name: langchain-agents-scaffold
description: Use when creating a new LangChain / LangGraph / DeepAgents project from scratch. Picks the right scaffolder for graphs vs. DeepAgents vs. LCEL chains.
---

# Scaffolding LangChain ecosystem projects

There is no single scaffolder that covers all three project shapes. Pick the right path:

| Project shape | Scaffolder |
|---|---|
| LangGraph agent (explicit StateGraph) | `langgraph new` (from `langgraph-cli`) |
| DeepAgents agent (planning + sub-agents + virtual FS) | No scaffolder — write ~15 lines yourself (recipe below) |
| LCEL pipeline (chains, RAG, classification) | No scaffolder — write ~10 lines yourself (recipe below) |

## LangGraph: `langgraph new`

```bash
pip install "langgraph-cli>=0.4"    # if not installed
langgraph new my-agent --template react-agent
cd my-agent
pip install -e .
```

`langgraph-cli` ships several templates. List them with `langgraph new --help`. Common picks:
- `react-agent` — single-LLM-with-tools loop. The most common starting point.
- `retrieval-agent` — RAG over a vector store.
- `memory-agent` — long-term memory using the LangGraph store.
- `data-enrichment-agent` — structured data extraction.

Each template ships its own `pyproject.toml`, `langgraph.json`, and `src/<package>/graph.py` — read those after scaffolding to learn the layout. **Do not assume the layout matches across templates.** The conventions vary.

## DeepAgents: write the file directly

There's no `deepagents new`. Create the project by hand:

```bash
mkdir my-deep-agent && cd my-deep-agent
python -m venv .venv && source .venv/bin/activate
pip install \
  "deepagents>=0.5.3" \
  "langchain>=1.2" \
  "langchain-anthropic>=1.4" \
  "langsmith>=0.7"
mkdir agent
```

Pin floors matter: `deepagents>=0.5` removed the legacy subagents API and added async sub-agents; `0.5.2` added the filesystem permissions system; `0.5.3` made `model=None` a deprecated kwarg (you must pass an explicit model) and added structured outputs for sub-agent responses.

Then `agent/__init__.py` (empty) and `agent/agent.py`:

```python
"""DeepAgent for my-deep-agent. Always exported as `agent`."""
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model

SYSTEM_PROMPT = "You are my-deep-agent, a helpful agent."

TOOLS = []          # add user tools here
SUBAGENTS = []      # add sub-agents here (see deepagents-code skill)

agent = create_deep_agent(
    model=init_chat_model("anthropic:claude-sonnet-4-6"),  # explicit model required as of 0.5.3
    tools=TOOLS,
    subagents=SUBAGENTS,
    instructions=SYSTEM_PROMPT,
)
```

Plus a `pyproject.toml` (or `requirements.txt`) and a `.env` with `ANTHROPIC_API_KEY` and `LANGSMITH_*`. That's the whole project.

For deploy: DeepAgents' `create_deep_agent` returns a compiled LangGraph, so a `langgraph.json` pointing at `agent.agent:agent` works for `langgraph dev` and `langgraph build/deploy`.

## LCEL chains: write the file directly

For non-agentic flows (RAG, summarization, classification):

```bash
mkdir my-chain && cd my-chain
python -m venv .venv && source .venv/bin/activate
pip install "langchain>=1.2" "langchain-openai>=1.0" "langsmith>=0.7"
mkdir agent
```

Then `agent/agent.py`:

```python
"""LCEL chain. Exposed as `agent` (a Runnable)."""
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda

SYSTEM_PROMPT = "You are a helpful assistant."

def _to_messages(payload: dict) -> list:
    msgs = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in payload.get("messages", []):
        msgs.append(HumanMessage(content=m["content"]))
    return msgs

agent = RunnableLambda(_to_messages) | init_chat_model("openai:gpt-4o-mini")
```

For RAG, see the `langchain-agents-langchain-code` skill.

## Naming conventions worth following (not enforced)

These are conventions, not requirements. They make follow-up work easier because every other skill in this bundle assumes them:

- The runnable artifact is named `agent` and lives at `agent/agent.py`.
- Provider keys and `LANGSMITH_*` go in `.env`. Commit a `.env.example`.
- Evalsets live under `evals/datasets/*.jsonl`; the eval runner at `evals/run.py`.
- A FastAPI host (if needed for Docker/Cloud Run deploy) lives at `server/app.py`.

Skills that follow assume these names. If the project diverges, adapt — these are not hard rules, just the path of least resistance.
