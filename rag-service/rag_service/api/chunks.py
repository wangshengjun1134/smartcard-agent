"""Chunk API endpoints for document chunking."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from rag_service.services.chunk_service import ChunkService
from rag_service.services.docling_chunker import parse_and_chunk_pdf, DocumentChunk
from rag_service.services.document_service import DocumentService
from rag_service.services.embedding_service import embedding_service
from rag_service.utils.database import get_storage_path
from rag_service.models.chunk import ChunkResponse, ChunkListResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chunks", tags=["chunks"])
chunk_service = ChunkService()
document_service = DocumentService()


# ===== Request/Response models =====

class ChunkRequest(BaseModel):
    """Request to chunk a document."""
    doc_id: str = Field(..., description="Document ID to chunk")
    kb_id: str = Field(..., description="Knowledge base ID")
    max_chars: int = Field(4000, ge=500, le=10000, description="Max chars per chunk")
    overlap: int = Field(200, ge=0, le=1000, description="Overlap chars between chunks")
    enable_ocr: bool = Field(False, description="Enable OCR for PDF parsing")
    enable_tables: bool = Field(False, description="Enable table structure recognition")
    auto_embed: bool = Field(False, description="Automatically start embedding after chunking")


class ChunkSummaryResponse(BaseModel):
    """Summary of chunking operation."""
    doc_id: str
    kb_id: str
    total_chunks: int
    max_heading_level: int
    page_range: dict
    headings: List[str]
    embedding_status: str = "pending"  # pending/embedding/embedded


class EmbedRequest(BaseModel):
    """Request to embed chunks."""
    doc_id: Optional[str] = Field(None, description="Document ID (optional, embed all if not specified)")
    kb_id: Optional[str] = Field(None, description="Knowledge base ID (optional)")
    batch_size: int = Field(50, ge=10, le=200, description="Batch size for embedding")


class EmbedResponse(BaseModel):
    """Response for embedding operation."""
    doc_id: Optional[str]
    kb_id: Optional[str]
    total: int
    success: int
    error: int
    message: str


# ===== Background Task =====

async def background_embed_task(
    doc_id: Optional[str] = None,
    kb_id: Optional[str] = None,
    batch_size: int = 50,
):
    """Background task for embedding chunks."""
    try:
        result = await embedding_service.embed_chunks(
            doc_id=doc_id,
            kb_id=kb_id,
            batch_size=batch_size,
        )
        logger.info(f"向量化完成: {result}")

        # 更新文档状态
        if doc_id:
            document_service.update_document_status(
                doc_id,
                status="embedded" if result["error"] == 0 else "partial_embedded",
            )
    except Exception as e:
        logger.exception(f"后台向量化失败: {e}")
        if doc_id:
            document_service.update_document_status(
                doc_id,
                status="embed_error",
                error_message=f"向量化失败: {str(e)}",
            )


# ===== API Endpoints =====

@router.post("/parse-and-chunk", response_model=ChunkSummaryResponse)
async def parse_and_chunk_document(
    request: ChunkRequest,
    background_tasks: BackgroundTasks,
):
    """解析 PDF 文档并分片

    使用 Docling 解析 PDF，按章节层级分片，结果存入数据库。
    返回分片摘要，不包含具体内容。

    **流程：**
    1. 验证文档存在且为 PDF
    2. 删除旧的分片（如果有）
    3. 解析 PDF + 分片
    4. 批量存入数据库（embedding_status='pending'）
    5. 更新文档状态
    6. 如果 auto_embed=True，后台启动向量化任务
    """
    # 1. 验证文档存在
    doc_info = document_service.get_document(request.doc_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail=f"文档不存在: {request.doc_id}")

    # 验证是 PDF（DocumentResponse 对象使用属性访问）
    if not (doc_info.mime_type or "").startswith("application/pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文档分片")

    # 验证 kb_id 匹配
    if doc_info.kb_id != request.kb_id:
        raise HTTPException(status_code=400, detail="文档不属于指定的知识库")

    # 2. 删除旧分片
    old_count = chunk_service.delete_chunks_by_document(request.doc_id)
    if old_count > 0:
        logger.info(f"删除旧分片: {old_count} 个")

    try:
        # 3. 解析 PDF + 分片
        relative_path = doc_info.file_path
        if not relative_path:
            raise HTTPException(status_code=404, detail="PDF 文件路径未设置")

        # 拼接绝对路径
        storage_root = get_storage_path()
        file_path = storage_root / relative_path

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF 文件不存在: {relative_path}")

        logger.info(f"开始解析 PDF: {doc_info.filename}")

        chunks = parse_and_chunk_pdf(
            file_path,
            max_chars=request.max_chars,
            overlap=request.overlap,
            enable_ocr=request.enable_ocr,
            enable_tables=request.enable_tables,
        )

        if not chunks:
            raise HTTPException(status_code=400, detail="分片结果为空")

        # 4. 批量存入数据库
        chunk_data_list = []
        for chunk in chunks:
            meta = {
                "overlap": chunk.overlap,
                "is_subchunk": chunk.is_subchunk,
            }

            chunk_data_list.append({
                "chunk_index": chunk.chunk_id,
                "content": chunk.text,
                "char_count": chunk.char_count,
                "heading": chunk.heading,
                "heading_level": chunk.heading_level,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "meta": meta,
            })

        created_chunks = chunk_service.create_chunks(
            doc_id=request.doc_id,
            kb_id=request.kb_id,
            chunks=chunk_data_list,
        )

        logger.info(f"分片入库完成: {len(created_chunks)} 个 chunk (embedding_status='pending')")

        # 5. 更新文档状态
        document_service.update_document_status(request.doc_id, status="chunked")

        # 6. 如果 auto_embed=True，启动后台向量化
        embedding_status = "pending"
        if request.auto_embed:
            background_tasks.add_task(
                background_embed_task,
                doc_id=request.doc_id,
                kb_id=request.kb_id,
                batch_size=50,
            )
            embedding_status = "embedding"
            logger.info(f"已向后台提交向量化任务: doc_id={request.doc_id}")

        # 7. 构建返回摘要
        headings = list(set(c.heading for c in created_chunks if c.heading != "(文档根)"))
        page_starts = [c.page_start for c in created_chunks if c.page_start > 0]
        page_ends = [c.page_end for c in created_chunks if c.page_end > 0]
        max_level = max((c.heading_level for c in created_chunks), default=0)

        return ChunkSummaryResponse(
            doc_id=request.doc_id,
            kb_id=request.kb_id,
            total_chunks=len(created_chunks),
            max_heading_level=max_level,
            page_range={
                "start": min(page_starts) if page_starts else 0,
                "end": max(page_ends) if page_ends else 0,
            },
            headings=sorted(headings),
            embedding_status=embedding_status,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"分片失败: {e}")
        document_service.update_document_status(
            request.doc_id,
            status="error",
            error_message=f"分片失败: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"分片失败: {str(e)}")


@router.post("/embed", response_model=EmbedResponse)
async def embed_chunks(
    request: EmbedRequest,
    background_tasks: BackgroundTasks,
):
    """向量化待处理的 chunks（后台任务）

    获取 embedding_status='pending' 的 chunks，向量化后存入 Qdrant 向量库。
    立即返回，后台执行。

    **参数：**
    - doc_id: 如果指定，只向量化该文档的 chunks
    - kb_id: 如果指定，只向量化该知识库的 chunks
    - 都不指定：向量化所有 pending chunks
    """
    # 统计 pending 数量
    if request.doc_id:
        pending = chunk_service.get_chunks_by_document(
            request.doc_id, embedding_status="pending"
        )
    elif request.kb_id:
        pending = chunk_service.get_chunks_by_knowledge_base(
            request.kb_id, embedding_status="pending", limit=1
        )
    else:
        pending = chunk_service.get_pending_chunks(limit=1)

    if not pending.chunks:
        return EmbedResponse(
            doc_id=request.doc_id,
            kb_id=request.kb_id,
            total=0,
            success=0,
            error=0,
            message="no pending chunks",
        )

    # 启动后台任务
    background_tasks.add_task(
        background_embed_task,
        doc_id=request.doc_id,
        kb_id=request.kb_id,
        batch_size=request.batch_size,
    )

    return EmbedResponse(
        doc_id=request.doc_id,
        kb_id=request.kb_id,
        total=pending.total,
        success=0,
        error=0,
        message=f"embedding started for {pending.total} chunks",
    )


@router.get("/by-document/{doc_id}", response_model=ChunkListResponse)
async def get_chunks_by_document(
    doc_id: str,
    embedding_status: Optional[str] = Query(None, description="Filter by embedding status"),
):
    """获取文档的所有分片"""
    return chunk_service.get_chunks_by_document(doc_id, embedding_status=embedding_status)


@router.get("/by-doc-heading", response_model=ChunkListResponse)
async def get_chunks_by_heading(
    doc_id: str = Query(..., description="Document ID"),
    heading: str = Query(..., description="Heading path (exact match or prefix)"),
):
    """按章节标题获取分片

    支持前缀匹配，如 "1 Introduction" 会返回所有以该标题开头的分片。
    """
    chunks = chunk_service.get_chunks_by_document(doc_id)

    # 过滤匹配的 heading
    matched = [
        c for c in chunks.chunks
        if c.heading == heading or c.heading.startswith(heading + " >") or c.heading.startswith(heading + " (")
    ]

    return ChunkListResponse(chunks=matched, total=len(matched))


@router.get("/by-page-range", response_model=ChunkListResponse)
async def get_chunks_by_page_range(
    doc_id: str = Query(..., description="Document ID"),
    page_start: int = Query(..., ge=1, description="Start page"),
    page_end: int = Query(..., ge=1, description="End page"),
):
    """按页码范围获取分片"""
    chunks = chunk_service.get_chunks_by_document(doc_id)

    # 过滤页码范围
    matched = [
        c for c in chunks.chunks
        if c.page_start >= page_start and c.page_end <= page_end
    ]

    return ChunkListResponse(chunks=matched, total=len(matched))


@router.get("/headings/{doc_id}", response_model=List[str])
async def get_document_headings(doc_id: str):
    """获取文档的所有章节标题列表"""
    chunks = chunk_service.get_chunks_by_document(doc_id)

    # 提取唯一标题，按层级排序
    headings = set()
    for c in chunks.chunks:
        if c.heading != "(文档根)":
            # 提取基础标题（去掉 " (part N)" 后缀）
            base_heading = c.heading.split(" (part ")[0]
            headings.add(base_heading)

    return sorted(headings)


@router.delete("/by-document/{doc_id}")
async def delete_chunks_by_document(doc_id: str):
    """删除文档的所有分片"""
    count = chunk_service.delete_chunks_by_document(doc_id)
    return {"deleted": count}
