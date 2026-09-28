from fastapi import APIRouter

from ..config import get_settings
from ..services.ollama import AgentLLM
from ..services.sandbox import docker_available

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict:
    s = get_settings()
    llm = AgentLLM()
    return {
        "status": "ok",
        "app_env": s.app_env,
        "llm": llm.name,
        "ollama_reachable": llm.reachable(),
        "mock_llm": llm.is_mock,
        "docker_available": docker_available(),
        "sandbox_mode": s.sandbox_mode,
        "require_human_approval": s.require_human_approval,
        "langfuse_enabled": s.langfuse_enabled,
    }
