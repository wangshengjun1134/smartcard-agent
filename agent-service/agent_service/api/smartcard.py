"""Smartcard API Router for APDU console.

This module provides endpoints for smartcard reader operations,
including listing readers and sending APDU commands.
"""

import logging
import traceback
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smartcard", tags=["smartcard"])


# ========== Models ==========

class ReaderInfo(BaseModel):
    """Smartcard reader information."""
    name: str
    connected: bool


class ReadersResponse(BaseModel):
    """Response containing list of readers."""
    readers: List[ReaderInfo]


class ApduRequest(BaseModel):
    """APDU command request."""
    reader: str
    apdu: str


class ApduResponse(BaseModel):
    """APDU command response."""
    reader: str
    apdu: str
    response: str
    duration: int  # milliseconds


class ConnectRequest(BaseModel):
    """Connect/disconnect request."""
    reader: str


class ConnectResponse(BaseModel):
    """Connect response."""
    reader: str
    connected: bool
    atr: str = ""  # ATR in hex format


# ========== Endpoints ==========

@router.get("/readers", response_model=ReadersResponse)
async def list_readers() -> ReadersResponse:
    """List available smartcard readers.

    Returns a list of detected smartcard readers with their connection status.

    Returns:
        ReadersResponse containing list of readers.
    """
    import traceback
    
    try:
        logger.info("Attempting to import pyscard...")
        from smartcard.System import readers
        logger.info("pyscard imported successfully")
        
        # 获取所有可用读卡器
        logger.info("Calling readers()...")
        available_readers = readers()
        logger.info(f"Found readers: {available_readers}")

        # 构建读卡器列表 (readers() 返回的是 PCSCReader 对象)
        # 通过尝试连接来判断读卡器当前是否有卡
        reader_list = []
        for r in available_readers:
            try:
                from smartcard.CardConnection import CardConnection
                conn = r.createConnection()
                conn.connect()
                # 连接成功说明有卡
                reader_list.append(ReaderInfo(name=r.name, connected=True))
                conn.disconnect()
            except Exception:
                # 连接失败说明无卡或未插入
                reader_list.append(ReaderInfo(name=r.name, connected=False))

        return ReadersResponse(readers=reader_list)
    except ImportError as e:
        logger.error(f"ImportError: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"pyscard not available: {str(e)}")
    except Exception as e:
        logger.error(f"Exception: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to list readers: {str(e)}")


@router.post("/connect", response_model=ConnectResponse)
async def connect_reader(request: ConnectRequest) -> ConnectResponse:
    """Connect to a smartcard reader.

    Args:
        request: Reader name to connect to.

    Returns:
        ConnectResponse with connection status.

    Raises:
        HTTPException: If reader not found or connection fails.
    """
    try:
        from agent_service.agents.tools.builtin import get_runtime_context
        from smartcard.System import readers

        ctx = get_runtime_context()
        if ctx is None:
            raise HTTPException(status_code=500, detail="Runtime context not initialized")

        client = ctx.pcsc_client
        if client is None:
            raise HTTPException(status_code=500, detail="No PCSC client attached")

        # 查找读卡器
        available_readers = readers()
        reader = next((r for r in available_readers if r.name == request.reader), None)
        if not reader:
            raise HTTPException(status_code=404, detail=f"Reader '{request.reader}' not found")

        # 检查是否已连接
        if ctx.connected and ctx.current_reader == request.reader:
            return ConnectResponse(reader=request.reader, connected=True, atr=ctx.atr.hex() if ctx.atr else "")

        # 断开旧连接
        if ctx.connected:
            client.disconnect()

        # 连接到指定读卡器（通过索引）
        reader_index = list(available_readers).index(reader)
        client.reader_index = reader_index
        atr = client.connect(reader_index)
        # pyscard getATR() returns list[int], convert to bytes
        atr_bytes = bytes(atr) if isinstance(atr, list) else atr
        atr_hex = atr_bytes.hex().upper()

        # 更新 RuntimeContext
        ctx.connect(request.reader, atr_bytes)

        logger.info(f"Connected to reader: {request.reader}, ATR: {atr_hex}")
        return ConnectResponse(reader=request.reader, connected=True, atr=atr_hex)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to connect reader: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")


@router.post("/disconnect", response_model=ConnectResponse)
async def disconnect_reader(request: ConnectRequest) -> ConnectResponse:
    """Disconnect from a smartcard reader.

    Args:
        request: Reader name to disconnect.

    Returns:
        ConnectResponse with connection status.
    """
    try:
        from agent_service.agents.tools.builtin import get_runtime_context

        ctx = get_runtime_context()
        if ctx is None or not ctx.connected:
            return ConnectResponse(reader=request.reader, connected=False)

        client = ctx.pcsc_client
        if client:
            try:
                client.disconnect()
            except Exception:
                pass

        ctx.disconnect()
        logger.info(f"Disconnected from reader: {request.reader}")
        return ConnectResponse(reader=request.reader, connected=False)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect reader: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


@router.post("/apdu", response_model=ApduResponse)
async def send_apdu(request: ApduRequest) -> ApduResponse:
    """Send APDU command to smartcard reader.

    Args:
        request: APDU command request containing reader name and APDU hex string.

    Returns:
        ApduResponse with response data and timing.

    Raises:
        HTTPException: If reader not found or command fails.
    """
    import time

    try:
        from agent_service.agents.tools.builtin import get_runtime_context

        ctx = get_runtime_context()
        if ctx is None:
            raise HTTPException(status_code=500, detail="Runtime context not initialized")

        if not ctx.connected:
            raise HTTPException(status_code=400, detail="Not connected to card")

        # 通过 RuntimeContext 发送 APDU
        start_time = time.time()
        response = ctx.send_apdu(request.apdu, check_sw=False)
        duration = int((time.time() - start_time) * 1000)

        response_hex = response.sw

        logger.info(f"APDU sent to {request.reader}, duration: {duration}ms")
        return ApduResponse(
            reader=request.reader,
            apdu=request.apdu,
            response=response_hex,
            duration=duration,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send APDU: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to send APDU: {str(e)}")
