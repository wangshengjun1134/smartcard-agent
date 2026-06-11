"""File API endpoints for knowledge base."""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import Optional

from rag_service.models.file import (
    FileNode,
    FileDetail,
    CreateFolderRequest,
    MoveFileRequest,
)
from rag_service.services.file_service import FileService


router = APIRouter()

# Create singleton file service instance
file_service = FileService()


@router.get("/tree")
async def get_file_tree() -> dict:
    """Get complete file tree structure.

    Returns:
        JSON response with file tree data.
    """
    try:
        tree = file_service.get_file_tree()
        return {"status": "ok", "data": tree}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    parent_id: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
) -> dict:
    """Upload a file to the knowledge base.

    Args:
        file: Uploaded file content.
        parent_id: Target folder ID (optional).
        name: Custom file name (optional).

    Returns:
        JSON response with uploaded file data.
    """
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

        # Upload file
        result = await file_service.upload_file(
            file_content=content,
            filename=file.filename or "unnamed",
            parent_id=parent_id,
            custom_name=name,
        )

        return {"status": "ok", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}")
async def get_file_detail(file_id: str) -> dict:
    """Get detailed information for a single file.

    Args:
        file_id: File ID to query.

    Returns:
        JSON response with file detail data.
    """
    try:
        detail = file_service.get_file_detail(file_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="File not found")
        return {"status": "ok", "data": detail}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/folder")
async def create_folder(request: CreateFolderRequest) -> dict:
    """Create a new folder.

    Args:
        request: Folder creation request with name and parent_id.

    Returns:
        JSON response with created folder data.
    """
    try:
        folder = await file_service.create_folder(
            name=request.name,
            parent_id=request.parent_id,
        )
        return {"status": "ok", "data": folder}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/move")
async def move_file(request: MoveFileRequest) -> dict:
    """Move a file or folder to a new location.

    Args:
        request: Move request with file_id and target_folder_id.

    Returns:
        JSON response with updated file data.
    """
    try:
        result = await file_service.move_file(
            file_id=request.file_id,
            target_folder_id=request.target_folder_id,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="File not found")
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))