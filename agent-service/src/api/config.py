"""API Configuration Router for LLM provider settings.

This module provides endpoints for managing and testing LLM API configurations.
"""

import time
import httpx
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.database import get_session_db_connection


router = APIRouter(prefix="/config", tags=["config"])


# ========== Models ==========

class ApiConfig(BaseModel):
    """API configuration model."""
    provider: str  # coding_plan, openai, deepseek, anthropic
    base_url: str
    api_key: str
    model: Optional[str] = None


class ApiConfigResponse(BaseModel):
    """API configuration response."""
    id: str
    provider: str
    base_url: str
    api_key: str  # Masked in responses
    model: Optional[str] = None
    created_at: int
    updated_at: int


class TestConnectionRequest(BaseModel):
    """Test connection request."""
    provider: str
    base_url: str
    api_key: str
    model: Optional[str] = None


class TestConnectionResponse(BaseModel):
    """Test connection response."""
    success: bool
    message: str
    latency_ms: Optional[int] = None


# ========== Helper Functions ==========

def mask_api_key(api_key: str) -> str:
    """Mask API key for display (show first 8 and last 4 chars)."""
    if len(api_key) <= 12:
        return api_key[:4] + "****"
    return api_key[:8] + "****" + api_key[-4:]


# ========== Endpoints ==========

@router.get("/api", response_model=Optional[ApiConfigResponse])
async def get_api_config() -> Optional[ApiConfigResponse]:
    """Get current API configuration.
    
    Returns the most recently updated configuration.
    """
    conn = get_session_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM api_config
        ORDER BY updated_at DESC
        LIMIT 1
        """
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return ApiConfigResponse(
        id=row["id"],
        provider=row["provider"],
        base_url=row["base_url"],
        api_key=mask_api_key(row["api_key"]),
        model=row["model"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post("/api", response_model=ApiConfigResponse)
async def save_api_config(config: ApiConfig) -> ApiConfigResponse:
    """Save API configuration.

    Creates a new config or updates existing one for the same provider.
    """
    from llm.config import LLMConfig

    now = int(time.time() * 1000)
    config_id = f"config-{now}"

    conn = get_session_db_connection()
    cursor = conn.cursor()

    # Check if config exists for this provider
    cursor.execute(
        "SELECT id FROM api_config WHERE provider = ?",
        (config.provider,)
    )
    existing = cursor.fetchone()

    if existing:
        # Update existing config
        cursor.execute(
            """
            UPDATE api_config
            SET base_url = ?, api_key = ?, model = ?, updated_at = ?
            WHERE provider = ?
            """,
            (config.base_url, config.api_key, config.model, now, config.provider)
        )
        config_id = existing["id"]
    else:
        # Insert new config
        cursor.execute(
            """
            INSERT INTO api_config (id, provider, base_url, api_key, model, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (config_id, config.provider, config.base_url, config.api_key, config.model, now, now)
        )

    conn.commit()
    conn.close()

    # Clear LLMConfig cache to force reload on next request
    LLMConfig.clear_cache()

    return ApiConfigResponse(
        id=config_id,
        provider=config.provider,
        base_url=config.base_url,
        api_key=mask_api_key(config.api_key),
        model=config.model,
        created_at=now,
        updated_at=now,
    )


@router.post("/api/test", response_model=TestConnectionResponse)
async def test_api_connection(request: TestConnectionRequest) -> TestConnectionResponse:
    """Test API connection.
    
    Sends a minimal request to verify the API key and endpoint are valid.
    """
    start_time = time.time()
    
    try:
        # Build headers based on provider
        headers = {}
        if request.provider == "anthropic":
            headers["x-api-key"] = request.api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["Authorization"] = f"Bearer {request.api_key}"
        
        headers["Content-Type"] = "application/json"
        
        # Build test request body
        model = request.model or "default"
        test_body = {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        }
        
        # Special handling for Anthropic
        if request.provider == "anthropic":
            test_body = {
                "model": model or "claude-3-haiku-20240307",
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "Hi"}],
            }
        
        # Make request
        endpoint = request.base_url.rstrip("/")
        if request.provider == "anthropic":
            url = f"{endpoint}/messages"
        else:
            url = f"{endpoint}/chat/completions"
        
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, headers=headers, json=test_body)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return TestConnectionResponse(
                success=True,
                message="连接成功",
                latency_ms=latency_ms,
            )
        elif response.status_code == 401:
            return TestConnectionResponse(
                success=False,
                message="API Key 无效",
                latency_ms=latency_ms,
            )
        elif response.status_code == 404:
            return TestConnectionResponse(
                success=False,
                message="端点不存在，请检查 Base URL",
                latency_ms=latency_ms,
            )
        else:
            error_msg = response.text[:100] if response.text else "未知错误"
            return TestConnectionResponse(
                success=False,
                message=f"连接失败 ({response.status_code}): {error_msg}",
                latency_ms=latency_ms,
            )
    
    except httpx.ConnectError:
        return TestConnectionResponse(
            success=False,
            message="无法连接到服务器，请检查 Base URL",
        )
    except httpx.TimeoutException:
        return TestConnectionResponse(
            success=False,
            message="连接超时",
        )
    except Exception as e:
        return TestConnectionResponse(
            success=False,
            message=f"测试失败: {str(e)}",
        )