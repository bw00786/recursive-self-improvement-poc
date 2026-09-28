# Development

## Prerequisites

- Python 3.12+, Node 20+
- Optional: Docker Desktop (sandbox isolation), Ollama + a Llama 3.1 model (real LLM)

## Setup

```bash
cd backend && pip install -e ".[dev]" && cd ..
python scripts/bootstrap.py          # champion v0.1.0 + baseline score
uvicorn backend.app.main:app --reload --port 8100
cd frontend && npm install && npm run dev   # http://localhost:5273
```

## Run one cycle without the UI

```bash
python scripts/run_experiment.py
```

## Tests

```bash
cd backend && pytest -q
```

Tests run fully offline: `MOCK_LLM=true`, `SANDBOX_MODE=local`, temp SQLite DB.

## Configuration

See `.env.example`. Key knobs: `OLLAMA_MODEL`, `MOCK_LLM` (auto/true/false),
`SANDBOX_MODE` (auto/docker/local), `MIN_SCORE_IMPROVEMENT`,
`HARD_MAX_LATENCY_SECONDS`, `EVAL_WEIGHTS` (JSON), `REQUIRE_HUMAN_APPROVAL`.

## Using a real Llama 3.1 model

```bash
ollama pull llama3.1:8b       # or any Llama 3.1 model
# .env: OLLAMA_MODEL=llama3.1:8b, MOCK_LLM=false
python scripts/bootstrap.py
```

## Docker sandbox image

```bash
docker build -t rail-sandbox:latest sandbox
```

Without the image, the backend falls back to local subprocess execution and
marks results `isolated=false`.
