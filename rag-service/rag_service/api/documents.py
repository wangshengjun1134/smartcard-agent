"""Document API endpoints for knowledge base."""

import hashlib
import mimetypes
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import Optional

from rag_service.models.document import DocumentResponse
from rag_service.services.document_service import DocumentService
from rag_service.services.knowledge_base_service import KnowledgeBaseService
from rag_service.utils.database import get_storage_path


router = APIRouter()

# Create singleton service instances
document_service = DocumentService()
kb_service = KnowledgeBaseService()


def _compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    kb_id: str = Form(...),
    folder_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    language: str = Form("zh"),
    tags: Optional[str] = Form(None),
    effective_from: Optional[str] = Form(None),
    effective_until: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),
) -> dict:
    """Upload a document to a knowledge base.

    Args:
        file: Uploaded file content.
        kb_id: Target knowledge base ID.
        title: Document title (optional, defaults to filename).
        source: Source description.
        language: Document language.
        tags: JSON array of tags.
        uploaded_by: User who uploaded.

    Returns:
        JSON response with uploaded document data.
    """
    # Validate knowledge base exists
    kb = kb_service.get_knowledge_base(kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    try:
        # Read file content
        content = await file.read()

        # Validate file size (100MB limit)
        max_size = 100 * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB"
            )

        # Compute file hash
        file_hash = _compute_sha256(content)

        # Build storage path
        storage_root = get_storage_path()
        storage_path = f"{kb_id}/{file_hash}_{file.filename}"

        # Save file to disk
        disk_path = storage_root / storage_path
        disk_path.parent.mkdir(parents=True, exist_ok=True)

        with open(disk_path, 'wb') as f:
            f.write(content)

        # Detect MIME type using mimetypes module (more accurate than file.content_type)
        detected_mime, _ = mimetypes.guess_type(file.filename or "unnamed")
        mime_type = detected_mime or file.content_type or "application/octet-stream"

        # Parse tags from JSON string
        import json
        parsed_tags = None
        if tags:
            try:
                parsed_tags = json.loads(tags)
            except json.JSONDecodeError:
                parsed_tags = [tags]

        # Create document record
        result = document_service.create_document(
            kb_id=kb_id,
            folder_id=folder_id,
            filename=file.filename or "unnamed",
            file_path=storage_path,
            file_size=len(content),
            mime_type=mime_type,
            file_hash=file_hash,
            title=title or (file.filename or "unnamed"),
            source=source,
            language=language,
            tags=parsed_tags,
            effective_from=effective_from,
            effective_until=effective_until,
            uploaded_by=uploaded_by,
        )

        if result is None:
            raise HTTPException(status_code=500, detail="Failed to create document record")

        return {"status": "ok", "data": result.model_dump()}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_documents(
    kb_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List documents with optional filters.

    Args:
        kb_id: Filter by knowledge base ID.
        status: Filter by document status.
        limit: Maximum number of results.
        offset: Offset for pagination.

    Returns:
        JSON response with document list.
    """
    try:
        result = document_service.list_documents(
            kb_id=kb_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return {
            "status": "ok",
            "data": {
                "documents": [d.model_dump() for d in result.documents],
                "total": result.total,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}")
async def get_document(doc_id: str) -> dict:
    """Get a document by ID.

    Args:
        doc_id: Document ID.

    Returns:
        JSON response with document data.
    """
    try:
        result = document_service.get_document(doc_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "ok", "data": result.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{doc_id}")
async def update_document(
    doc_id: str,
    title: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
) -> dict:
    """Update document metadata.

    Args:
        doc_id: Document ID.
        title: New title.
        source: New source.
        language: New language.
        tags: JSON array of new tags.

    Returns:
        JSON response with updated document data.
    """
    try:
        import json
        parsed_tags = None
        if tags:
            try:
                parsed_tags = json.loads(tags)
            except json.JSONDecodeError:
                parsed_tags = [tags]

        result = document_service.update_document(
            doc_id=doc_id,
            title=title,
            source=source,
            language=language,
            tags=parsed_tags,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "ok", "data": result.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(doc_id: str) -> dict:
    """Soft delete a document.

    Args:
        doc_id: Document ID.

    Returns:
        JSON response with deletion status.
    """
    try:
        result = document_service.delete_document(doc_id)
        if not result:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
