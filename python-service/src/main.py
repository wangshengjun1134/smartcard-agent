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

from api import files, rag, agent, session, config, smartcard, events
from utils.database import init_knowledge_database, init_session_database
from config.logging import setup_logging

# Initialize logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Initializes databases, preloads embeddings model, and sets up PCSC runtime context.
    """
    import asyncio
    from llm.embeddings import get_embeddings
    from runtime.context import RuntimeContext
    from tools.pcsc.client import PcscClient
    from agents.tools.builtin import set_runtime_context

    # Initialize databases on startup
    init_knowledge_database()
    init_session_database()

    # Preload embeddings model in thread pool to avoid blocking
    print("Preloading embeddings model...")
    await asyncio.to_thread(get_embeddings)
    print("Embeddings model loaded successfully")

    # Create shared runtime context with PCSC client
    print("Initializing PCSC runtime context...")
    ctx = RuntimeContext()
    client = PcscClient()
    ctx.attach_client(client)
    set_runtime_context(ctx)

    # Register APDU event listener for WebSocket broadcasting
    from api.events import emit_apdu_event
    ctx.add_apdu_listener(emit_apdu_event)
    print("APDU event listener registered (WebSocket broadcaster)")

    print("PCSC runtime context initialized")

    # Discover and register skill plugins
    print("Discovering skill plugins...")
    from skills.registry_extension import discover_and_register_skills
    registered = discover_and_register_skills()
    print(f"Skill plugins registered: {len(registered)} skills")

    yield

    # Cleanup on shutdown
    print("Shutting down PCSC client...")
    try:
        if ctx.pcsc_client:
            ctx.pcsc_client.disconnect()
    except Exception:
        pass


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

# Include Smartcard API router
app.include_router(smartcard.router, prefix="/api")

# Include WebSocket events router (no prefix - endpoint is /ws/apdu)
app.include_router(events.router)


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