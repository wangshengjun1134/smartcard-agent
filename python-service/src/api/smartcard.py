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
        # TODO: 使用 pyscard 发送真实 APDU 命令
        # from smartcard.System import readers
        # from smartcard.CardConnection import CardConnection
        # 
        # available_readers = readers()
        # if request.reader not in available_readers:
        #     raise HTTPException(status_code=404, detail=f"Reader '{request.reader}' not found")
        # 
        # # 连接读卡器
        # reader_index = available_readers.index(request.reader)
        # card_connection = readers()[reader_index].createConnection()
        # card_connection.connect()
        # 
        # # 解析 APDU
        # apdu_bytes = bytes.fromhex(request.apdu.replace(" ", ""))
        # 
        # # 发送命令
        # start_time = time.time()
        # response = card_connection.transmit(list(apdu_bytes))
        # duration = int((time.time() - start_time) * 1000)
        # 
        # # 格式化响应
        # response_hex = " ".join(f"{b:02X}" for b in response[0])
        
        # 临时模拟响应
        time.sleep(0.05)  # 模拟延迟
        duration = 50
        
        cleaned = request.apdu.replace(" ", "")
        resp_len = min(len(cleaned) // 2, 20)
        import random
        response_hex = " ".join(
            f"{random.randint(0, 255):02X}" for _ in range(resp_len)
        ) + " 90 00"
        
        return ApduResponse(
            reader=request.reader,
            apdu=request.apdu,
            response=response_hex,
            duration=duration,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send APDU: {str(e)}")
