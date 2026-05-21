"""Agent API Router for agent chat endpoints.

This module provides the FastAPI router for agent-related endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from agents.graph.workflow import run_agent, run_agent_async


router = APIRouter(prefix="/agent", tags=["agent"])


class AgentChatRequest(BaseModel):
    """Agent chat request model."""

    message: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class AgentChatResponse(BaseModel):
    """Agent chat response model."""

    response: str
    execution_intent: str
    goal: str
    observations: List[Dict[str, Any]]
    success: bool
    error: Optional[str] = None


class AgentStatusResponse(BaseModel):
    """Agent status response model."""

    status: str
    skills_registered: int
    capabilities: List[str]


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest) -> AgentChatResponse:
    """Chat with the agent.

    Args:
        request: Chat request with message

    Returns:
        Agent response with execution results.
    """
    try:
        # Run agent
        result = await run_agent_async(request.message)

        return AgentChatResponse(
            response=result.get("final_response", ""),
            execution_intent=result.get("execution_intent", ""),
            goal=result.get("current_goal", ""),
            observations=result.get("observations", []),
            success=result.get("finished", False) and not result.get("error"),
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=AgentStatusResponse)
async def agent_status() -> AgentStatusResponse:
    """Get agent status.

    Returns:
        Agent status information.
    """
    from skills.base.registry import get_registry

    registry = get_registry()

    return AgentStatusResponse(
        status="running",
        skills_registered=len(registry.list_skills()),
        capabilities=registry.list_categories(),
    )


@router.get("/skills")
async def list_skills() -> Dict[str, Any]:
    """List all registered skills.

    Returns:
        Dictionary of skill metadata.
    """
    from skills.base.registry import get_registry

    registry = get_registry()

    return registry.get_all_metadata()


@router.get("/skills/{skill_name}")
async def get_skill_info(skill_name: str) -> Dict[str, Any]:
    """Get information about a specific skill.

    Args:
        skill_name: Skill name

    Returns:
        Skill metadata.
    """
    from skills.base.registry import get_registry

    registry = get_registry()
    skill = registry.get_skill(skill_name)

    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    return skill.get_metadata()


@router.post("/connect")
async def connect_card() -> Dict[str, Any]:
    """Connect to smart card reader.

    Returns:
        Connection result with ATR.
    """
    from tools.pcsc.client import PcscClient
    from tools.pcsc.exceptions import ReaderNotFoundError, CardNotFoundError

    client = PcscClient()

    try:
        atr = client.connect()
        return {
            "success": True,
            "reader": client.reader_name,
            "atr": atr.hex().upper(),
        }
    except ReaderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect_card() -> Dict[str, Any]:
    """Disconnect from smart card reader.

    Returns:
        Disconnect result.
    """
    from tools.pcsc.client import PcscClient

    # Note: In real implementation, this would use the client from session
    # For now, return success
    return {"success": True, "message": "Disconnected"}