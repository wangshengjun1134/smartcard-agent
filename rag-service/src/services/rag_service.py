"""RAG (Retrieval-Augmented Generation) service."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from llm import get_llm, LLMConfig
from vectordb import QdrantStore, VectorDBConfig


# RAG prompt template
RAG_PROMPT_TEMPLATE = """你是一个智能卡知识库助手。根据以下检索到的知识内容回答用户问题。

如果检索到的内容与问题相关，请基于这些内容回答。
如果检索到的内容与问题不相关或不足以回答问题，请诚实地说明你无法找到相关信息。

检索到的知识内容：
{context}

用户问题：{question}

回答："""


class RAGService:
    """RAG service for knowledge base question answering."""

    def __init__(
        self,
        vectordb_config: Optional[VectorDBConfig] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        """Initialize RAG service.

        Args:
            vectordb_config: Vector database configuration.
            llm_config: LLM configuration.
        """
        self.llm_config = llm_config or LLMConfig.get_config()
        self.vectordb_config = vectordb_config or VectorDBConfig.from_env()
        self._store: Optional[QdrantStore] = None
        self._chain = None

    def _get_store(self) -> QdrantStore:
        """Get or create vector store."""
        if self._store is None:
            self._store = QdrantStore(
                config=self.vectordb_config,
                llm_config=self.llm_config,
            )
        return self._store

    def _get_chain(self):
        """Get or create RAG chain."""
        if self._chain is None:
            store = self._get_store()
            vector_store = store.get_vector_store()

            llm = get_llm(self.llm_config)
            prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

            retriever = vector_store.as_retriever(search_kwargs={"k": 4})

            def format_docs(docs: List[Document]) -> str:
                """Format retrieved documents into context string."""
                return "\n\n---\n\n".join(
                    f"来源: {doc.metadata.get('source', '未知')}\n内容: {doc.page_content}"
                    for doc in docs
                )

            self._chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
        return self._chain

    async def add_knowledge(
        self,
        content: str,
        source: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Add knowledge to the vector store.

        Args:
            content: Knowledge content text.
            source: Source identifier (file name, URL, etc).
            metadata: Additional metadata.

        Returns:
            Document ID.
        """
        store = self._get_store()

        full_metadata = {"source": source}
        if metadata:
            full_metadata.update(metadata)

        ids = await store.add_texts([content], metadatas=[full_metadata])
        return ids[0] if ids else ""

    async def add_documents(
        self,
        documents: List[Document],
    ) -> List[str]:
        """Add documents to the vector store.

        Args:
            documents: List of documents to add.

        Returns:
            List of document IDs.
        """
        store = self._get_store()
        return await store.add_documents(documents)

    async def query(
        self,
        question: str,
        k: int = 4,
    ) -> str:
        """Query the knowledge base using RAG.

        Args:
            question: User question.
            k: Number of documents to retrieve.

        Returns:
            Generated answer.
        """
        chain = self._get_chain()
        answer = await chain.ainvoke(question)
        return answer

    async def search(
        self,
        query: str,
        k: int = 4,
    ) -> List[tuple[Document, float]]:
        """Search for relevant documents without generation.

        Args:
            query: Search query.
            k: Number of results to return.

        Returns:
            List of (document, score) tuples.
        """
        store = self._get_store()
        return await store.similarity_search_with_score(query, k=k)

    def delete_collection(self) -> None:
        """Delete the knowledge collection."""
        store = self._get_store()
        store.delete_collection()
        self._chain = None