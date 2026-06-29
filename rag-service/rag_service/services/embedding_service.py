"""Embedding service for chunk vectorization.

Connects pending chunks from the database to the Qdrant vector store.
Handles batch embedding and status tracking.
"""

import asyncio
import logging
from typing import Optional, List, Tuple

from rag_service.services.chunk_service import ChunkService
from rag_service.services.processing_log_service import ProcessingLogService
from rag_service.llm.embeddings import get_embeddings
from rag_service.vectordb.qdrant_store import QdrantStore
from rag_service.models.chunk import ChunkResponse


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for embedding chunks into the vector store."""

    def __init__(self):
        self.chunk_service = ChunkService()
        self.log_service = ProcessingLogService()
        self._qdrant_store: Optional[QdrantStore] = None
        self._embeddings = None

    @property
    def qdrant_store(self) -> QdrantStore:
        if self._qdrant_store is None:
            self._qdrant_store = QdrantStore()
        return self._qdrant_store

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = get_embeddings()
        return self._embeddings

    async def embed_chunks(
        self,
        doc_id: Optional[str] = None,
        kb_id: Optional[str] = None,
        batch_size: int = 50,
    ) -> dict:
        """向量化待处理的 chunks
        
        Args:
            doc_id: 如果指定，只向量化该文档的 chunks
            kb_id: 如果指定，只向量化该知识库的 chunks
            batch_size: 每批处理的 chunk 数量
        
        Returns:
            处理结果统计
        """
        # 获取待向量化的 chunks
        pending_chunks = self._get_pending_chunks(doc_id, kb_id)
        
        if not pending_chunks:
            logger.info("没有待向量化的 chunks")
            return {"total": 0, "success": 0, "error": 0, "message": "no pending chunks"}

        total = len(pending_chunks)
        success_count = 0
        error_count = 0

        logger.info(f"开始向量化 {total} 个 chunks (batch_size={batch_size})")

        # 创建处理日志
        log_result = self.log_service.create_log(
            doc_id=doc_id or "batch",
            action="embed",
            status="started",
            details={"message": f"Starting embedding for {total} chunks"},
        )
        log_id = log_result.id if log_result else None

        # 分批处理
        for i in range(0, total, batch_size):
            batch = pending_chunks[i:i + batch_size]
            
            try:
                batch_success, batch_errors = await self._embed_batch(batch)
                success_count += batch_success
                error_count += batch_errors
                
                logger.info(
                    f"进度: {min(i + batch_size, total)}/{total} "
                    f"(成功: {success_count}, 失败: {error_count})"
                )
            except Exception as e:
                logger.exception(f"批次 {i // batch_size + 1} 向量化失败: {e}")
                error_count += len(batch)
                # 标记该批次为错误
                for chunk in batch:
                    self.chunk_service.update_chunk_status(
                        chunk.id, "error"
                    )

        # 更新处理日志
        if log_id:
            self.log_service.update_log(
                log_id=log_id,
                status="success" if error_count == 0 else "failed",
                details={"message": f"Completed: {success_count} success, {error_count} errors"},
            )

        return {
            "total": total,
            "success": success_count,
            "error": error_count,
        }

    def _get_pending_chunks(
        self,
        doc_id: Optional[str] = None,
        kb_id: Optional[str] = None,
    ) -> List[ChunkResponse]:
        """获取待向量化的 chunks"""
        if doc_id:
            return self.chunk_service.get_chunks_by_document(
                doc_id, embedding_status="pending"
            ).chunks
        elif kb_id:
            return self.chunk_service.get_chunks_by_knowledge_base(
                kb_id, embedding_status="pending", limit=10000
            ).chunks
        else:
            return self.chunk_service.get_pending_chunks(limit=10000)

    async def _embed_batch(
        self, chunks: List[ChunkResponse]
    ) -> Tuple[int, int]:
        """向量化一个批次的 chunks
        
        Returns:
            (success_count, error_count)
        """
        if not chunks:
            return 0, 0

        # 准备文本和元数据
        texts = []
        metadatas = []
        chunk_map = {}  # index -> chunk

        for i, chunk in enumerate(chunks):
            if not chunk.content.strip():
                # 跳过空内容
                self.chunk_service.update_chunk_status(chunk.id, "error")
                continue

            texts.append(chunk.content)
            metadatas.append({
                "chunk_id": chunk.id,
                "doc_id": chunk.doc_id,
                "kb_id": chunk.kb_id,
                "chunk_index": chunk.chunk_index,
                "heading": chunk.heading,
                "heading_level": chunk.heading_level,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "char_count": chunk.char_count,
            })
            chunk_map[i] = chunk

        if not texts:
            return 0, len(chunks)

        try:
            # 添加到向量库（内部会调用 embeddings.embed_documents）
            ids = await self.qdrant_store.add_texts(texts, metadatas)

            # 更新状态为 embedded
            for chunk_id in ids:
                # 从 chunk_map 中找到对应的 chunk
                for idx, chunk in chunk_map.items():
                    if chunk.id == chunk_id:
                        self.chunk_service.update_chunk_status(
                            chunk_id, "embedded"
                        )
                        break

            return len(ids), len(chunks) - len(ids)

        except Exception as e:
            logger.exception(f"批次向量化失败: {e}")
            # 标记所有为错误
            for chunk in chunks:
                self.chunk_service.update_chunk_status(chunk.id, "error")
            return 0, len(chunks)


# 全局单例
embedding_service = EmbeddingService()
