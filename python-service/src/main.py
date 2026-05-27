#!/usr/bin/env python3
"""
Smartcard Knowledge Base Service - FastAPI Entry Point.

This module provides the HTTP API entry point for the Python service that runs
as a standalone HTTP server, communicating with the frontend via REST API.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import files, rag, agent, session, config
from utils.database import init_knowledge_database, init_session_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Initializes databases and preloads embeddings model on startup.
    """
    import asyncio
    from llm.embeddings import get_embeddings
    from llm.config import LLMConfig
    from llm.llm import get_llm

    # Initialize databases on startup
    init_knowledge_database()
    init_session_database()

    # Preload LLM config (warm up database connection)
    print("Preloading LLM config...")
    config = LLMConfig.get_config()
    print(f"LLM config loaded: model={config.openai_model}")

    # Preload LLM instance
    print("Preloading LLM instance...")
    await asyncio.to_thread(get_llm)
    print("LLM instance loaded successfully")

    # Preload embeddings model in thread pool to avoid blocking
    print("Preloading embeddings model...")
    await asyncio.to_thread(get_embeddings)
    print("Embeddings model loaded successfully")

    yield


app = FastAPI(
    title="Smartcard Knowledge Base Service",
    description="Python backend service for knowledge base file management",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include file API router
app.include_router(files.router, prefix="/api/files")

# Include RAG API router
app.include_router(rag.router, prefix="/api")

# Include Agent API router
app.include_router(agent.router, prefix="/api")

# Include Session API router
app.include_router(session.router, prefix="/api")

# Include Config API router
app.include_router(config.router, prefix="/api")


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Status information.
    """
    return {"status": "ok", "service": "knowledge-base", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)