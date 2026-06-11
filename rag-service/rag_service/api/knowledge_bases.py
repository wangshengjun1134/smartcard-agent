"""Knowledge base API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from rag_service.services.knowledge_base_service import KnowledgeBaseService


router = APIRouter()

kb_service = KnowledgeBaseService()


class KnowledgeBaseCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class KnowledgeBaseUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.get("/list")
async def list_knowledge_bases() -> dict:
    """List all knowledge bases."""
    try:
        result = kb_service.list_knowledge_bases()
        return {
            "status": "ok",
            "data": [kb.model_dump() for kb in result],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_knowledge_base(request: KnowledgeBaseCreateRequest) -> dict:
    """Create a new knowledge base."""
    try:
        result = kb_service.create_knowledge_base(
            name=request.name,
            description=request.description,
        )
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to create knowledge base")
        return {"status": "ok", "data": result.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{kb_id}")
async def get_knowledge_base(kb_id: str) -> dict:
    """Get a knowledge base by ID."""
    try:
        result = kb_service.get_knowledge_base(kb_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return {"status": "ok", "data": result.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{kb_id}")
async def update_knowledge_base(kb_id: str, request: KnowledgeBaseUpdateRequest) -> dict:
    """Update a knowledge base."""
    try:
        result = kb_service.update_knowledge_base(
            kb_id=kb_id,
            name=request.name,
            description=request.description,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return {"status": "ok", "data": result.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str) -> dict:
    """Delete a knowledge base."""
    try:
        result = kb_service.delete_knowledge_base(kb_id)
        if not result:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
