"""RAIL backend entry point."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import benchmark, candidates, champions, evaluations, experiments, health, mcp, metrics
from .config import get_settings
from .database import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("rail")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="RAIL — Recursive AI Improvement Laboratory", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5273", "http://127.0.0.1:5273",
            "http://localhost:5173", "http://127.0.0.1:5173",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Optional OpenTelemetry — the app runs fine without it.
    if settings.otel_enabled:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
        except Exception as exc:  # noqa: BLE001
            log.info("OpenTelemetry instrumentation skipped: %s", exc)

    for r in (health.router, champions.router, experiments.router, candidates.router,
              evaluations.router, metrics.router, benchmark.router, mcp.router):
        app.include_router(r)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()
        if settings.langfuse_enabled:
            log.info("Langfuse enabled at %s", settings.langfuse_host)

    return app


app = create_app()
