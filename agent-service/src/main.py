#!/usr/bin/env python3
"""Agent Service - Smart Card Operation Agent FastAPI Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import agent, session, config, smartcard, events
from utils.database import init_session_database
from config.logging import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Initializes session database, PCSC runtime context, and skill plugins.
    """
    import asyncio
    from runtime.context import RuntimeContext
    from tools.pcsc.client import PcscClient
    from agents.tools.builtin import set_runtime_context

    # Initialize session database
    init_session_database()

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
    title="Agent Service",
    description="Smart card operation agent with reasoning loop",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(agent.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(smartcard.router, prefix="/api")

# Include WebSocket events router (no prefix - endpoint is /ws/apdu)
app.include_router(events.router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "agent", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)