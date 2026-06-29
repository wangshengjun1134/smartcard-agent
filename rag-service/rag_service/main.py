#!/usr/bin/env python3
"""RAG Service - Knowledge Base FastAPI Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag_service.api import files, rag, documents, knowledge_bases, chunks
from rag_service.utils.database import init_knowledge_database
from rag_service.config.logging import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Initializes database and preloads embedding model.
    """
    import asyncio

    # Initialize database
    init_knowledge_database()

    # Preload embedding model
    print("Preloading embedding model...")
    try:
        from rag_service.llm.embeddings import get_embeddings
        await asyncio.to_thread(get_embeddings)
        print("Embedding model loaded successfully")
    except Exception as e:
        print(f"Warning: Failed to load embedding model: {e}")
        print("RAG service will continue without embedding functionality")

    yield

    # Cleanup
    print("RAG service shutting down...")


app = FastAPI(
    title="RAG Service",
    description="Knowledge base file management and retrieval",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",    # Tauri dev server
        "http://127.0.0.1:1420",    # Tauri dev server (IP)
        "tauri://localhost",        # Tauri production
        "http://localhost:5173",    # Vite dev server
        "http://127.0.0.1:5173",    # Vite dev server (IP)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(files.router, prefix="/api/files")
app.include_router(documents.router, prefix="/api/documents")
app.include_router(knowledge_bases.router, prefix="/api/knowledge-bases")
app.include_router(chunks.router)  # chunks router has its own prefix
app.include_router(rag.router, prefix="/api")


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "rag", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)