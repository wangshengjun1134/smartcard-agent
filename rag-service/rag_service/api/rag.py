"""RAG API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rag_service.services.rag_service import RAGService


router = APIRouter(prefix="/rag", tags=["rag"])

# Global RAG service instance
_rag_service: RAGService = None


def get_rag_service() -> RAGService:
    """Get or create RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


class AddKnowledgeRequest(BaseModel):
    """Request model for adding knowledge."""

    content: str
    source: str
    metadata: dict = None


class QueryRequest(BaseModel):
    """Request model for querying knowledge."""

    question: str
    k: int = 4


class SearchResult(BaseModel):
    """Search result model."""

    content: str
    source: str
    score: float
    metadata: dict = None


class QueryResponse(BaseModel):
    """Response model for query."""

    answer: str


@router.post("/add", response_model=dict)
async def add_knowledge(request: AddKnowledgeRequest):
    """Add knowledge to the vector store."""
    try:
        service = get_rag_service()
        doc_id = await service.add_knowledge(
            content=request.content,
            source=request.source,
            metadata=request.metadata,
        )
        return {"id": doc_id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """Query the knowledge base."""
    try:
        service = get_rag_service()
        answer = await service.query(request.question, k=request.k)
        return QueryResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=list[SearchResult])
async def search_knowledge(request: QueryRequest):
    """Search for relevant documents."""
    try:
        service = get_rag_service()
        results = await service.search(request.question, k=request.k)
        return [
            SearchResult(
                content=doc.page_content,
                source=doc.metadata.get("source", "未知"),
                score=score,
                metadata=doc.metadata,
            )
            for doc, score in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collection")
async def delete_collection():
    """Delete the knowledge collection."""
    try:
        service = get_rag_service()
        service.delete_collection()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_collection_info():
    """Get collection information."""
    try:
        service = get_rag_service()
        store = service._get_store()
        info = store.get_collection_info()
        return {
            "points_count": info.points_count,
            "status": info.status,
            "config": info.config,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))