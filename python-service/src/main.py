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

from api import files, rag, agent, session
from utils.database import init_knowledge_database, init_session_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Initializes databases on startup.
    """
    # Initialize databases on startup
    init_knowledge_database()
    init_session_database()
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