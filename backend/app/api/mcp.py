from fastapi import APIRouter, HTTPException

from ..schemas import McpCallRequest
from ..tools import registry

router = APIRouter(tags=["mcp"])


@router.get("/api/mcp/tools")
def mcp_tools() -> list[dict]:
    return registry.list_tools()


@router.post("/api/mcp/call")
def mcp_call(body: McpCallRequest):
    try:
        return {"result": registry.call_tool(body.name, body.arguments)}
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"tool failed: {exc}") from exc
