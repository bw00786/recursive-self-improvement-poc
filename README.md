# RAIL — Recursive AI Improvement Laboratory

A controlled proof-of-concept demonstrating **measurable, human-supervised recursive
self-improvement** of an AI agent.

```
HUMAN OBJECTIVE
      │
      ▼
IMPROVEMENT AGENT (Llama 3.1 via Ollama)
      │
      ├── Analyze failures
      ├── Research techniques
      └── Generate candidate
      │
      ▼
GIT CANDIDATE WORKSPACE
      │
      ▼
DOCKER SANDBOX  ──►  IMMUTABLE EVALUATOR
      │
      ▼
COMPARE WITH CHAMPION
      │
  ┌───┴────┐
  ▼        ▼
REJECT   HUMAN APPROVAL ──► NEW CHAMPION ──► repeat
```

The LLM **proposes** changes. The **sandbox** tests them. The **evaluator** decides.
A **human** approves promotion. The improvement agent never touches production, the
benchmark, the evaluator, or the promotion rules.

## Stack

| Component | Technology |
|---|---|
| LLM | Llama 3.1 via Ollama (configurable, CPU-only OK) |
| Agent loop | LangGraph |
| Backend | FastAPI + SQLAlchemy + Pydantic |
| Frontend | React + TypeScript + Vite + Material UI |
| Database | PostgreSQL + pgvector (SQLite fallback for local dev) |
| Sandbox | Docker |
| Observability | OpenTelemetry, optional Langfuse |
| Tool layer | MCP-compatible HTTP tools |

## Quick start (local, no Docker required for the core loop)

Prereqs: Python 3.12+, Node 20+, optionally Ollama with a Llama 3.1 model.

```bash
# 1. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # or source .venv/bin/activate
pip install -e ".[dev]"
cd ..

# 2. Bootstrap champion v0.1.0 and run the baseline benchmark
python scripts/bootstrap.py

# 3. Start the API
uvicorn backend.app.main:app --reload --port 8100

# 4. Frontend
cd frontend
npm install
npm run dev          # http://localhost:5273
```

Open the dashboard, click **Start Improvement Cycle**, watch the loop run, then
approve or reject the candidate in the **Approvals** queue.

> **No GPU / no Ollama?** The system ships with a deterministic mock LLM mode
> (`MOCK_LLM=true`, the default when Ollama is unreachable) so the entire loop —
> hypothesis, candidate, sandbox, evaluation, promotion — runs offline.

## Full stack with Docker

```bash
cp .env.example .env        # edit OLLAMA_MODEL etc.
docker compose up -d postgres ollama
docker compose up -d backend frontend
docker compose exec ollama ollama pull llama3.1:8b   # or your configured model
```

## Demo scenario

1. `python scripts/bootstrap.py` → Champion v0.1.0 with baseline score.
2. Dashboard → **Start Improvement Cycle**.
3. Llama 3.1 analyzes failures, hypothesizes (e.g. "hybrid retrieval improves recall"),
   generates a candidate, runs it in the sandbox against the immutable benchmark.
4. UI shows score delta (e.g. 78.4 → 84.7) → **APPROVE** → Champion v0.2.0.
5. Repeat. The second cycle sees the first cycle's history — strategy statistics
   accumulate, and the improvement agent starts prioritizing strategies that have
   worked before. That is the recursive loop.

## Layout

```
backend/     FastAPI app, LangGraph loop, services, agents, MCP tools
frontend/    React/Vite control-plane dashboard
sut/         System under test (the QA agent that gets improved)
benchmark/   Immutable benchmark + evaluator (candidates cannot modify)
sandbox/     Docker image for candidate execution
experiments/ champion/ and candidates/ workspaces
prompts/     Agent prompts
scripts/     bootstrap / run helpers
docs/        architecture, security, api, development
```

See [docs/development.md](docs/development.md) for the full guide.
