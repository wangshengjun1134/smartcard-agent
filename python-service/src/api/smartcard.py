"""Smartcard API Router for APDU console.

This module provides endpoints for smartcard reader operations,
including listing readers and sending APDU commands.
"""

import logging
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


# 存储读卡器连接会话
_reader_connections: dict = {}


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
        from smartcard.System import readers
        from smartcard.Exceptions import CardConnectionException

        available_readers = readers()
        reader = next((r for r in available_readers if r.name == request.reader), None)
        if not reader:
            raise HTTPException(status_code=404, detail=f"Reader '{request.reader}' not found")

        # 检查是否已连接
        if request.reader in _reader_connections:
            return ConnectResponse(reader=request.reader, connected=True)

        # 创建连接
        conn = reader.createConnection()
        conn.connect()
        _reader_connections[request.reader] = conn

        # 获取 ATR - 有些读卡器需要短暂延迟才能返回 ATR
        import time
        time.sleep(0.2)
        atr_bytes = conn.getATR()
        logger.info(f"ATR bytes: {atr_bytes}")

        # 如果第一次没拿到，重试一次
        if not atr_bytes:
            time.sleep(0.3)
            atr_bytes = conn.getATR()
            logger.info(f"ATR bytes (retry): {atr_bytes}")

        atr_hex = " ".join(f"{b:02X}" for b in atr_bytes) if atr_bytes else "N/A"

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

    Raises:
        HTTPException: If reader not found or not connected.
    """
    try:
        if request.reader not in _reader_connections:
            return ConnectResponse(reader=request.reader, connected=False)

        # 断开连接
        conn = _reader_connections.pop(request.reader)
        try:
            conn.disconnect()
        except Exception:
            pass  # 忽略断开时的异常

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
        # 优先使用已建立的连接
        if request.reader in _reader_connections:
            conn = _reader_connections[request.reader]
        else:
            # 如果没有连接，查找读卡器并临时连接
            from smartcard.System import readers
            available_readers = readers()
            reader = next((r for r in available_readers if r.name == request.reader), None)
            if not reader:
                raise HTTPException(status_code=404, detail=f"Reader '{request.reader}' not found")
            conn = reader.createConnection()
            conn.connect()

        # 解析 APDU
        cleaned = request.apdu.replace(" ", "")
        apdu_bytes = bytes.fromhex(cleaned)

        # 发送命令
        start_time = time.time()
        response, sw1, sw2 = conn.transmit(list(apdu_bytes))
        duration = int((time.time() - start_time) * 1000)

        # 格式化响应: 数据 + SW1 SW2
        response_hex = " ".join(f"{b:02X}" for b in response) + f" {sw1:02X} {sw2:02X}"

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
