# Agent Service

智能卡操作 Agent 服务

## 功能

- Agent 推理循环（工具调用）
- 智能卡操作（PCSC）
- 会话管理
- WebSocket APDU 事件广播

## 运行

```bash
# 安装依赖
pip install -e .

# 运行服务（在 agent-service 目录下）
python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8001 --reload
```

## API 端点

- `POST /api/agent/chat/stream` - Agent 聊天（SSE 流）
- `GET /api/session/list` - 会话列表
- `POST /api/smartcard/connect` - 连接读卡器
- `WS /ws/apdu` - APDU 事件 WebSocket
- `GET /health` - 健康检查

## 数据目录

- `data/session.db` - 会话数据库
- `data/checkpoints/` - 状态检查点
- `.skills/` - 技能插件目录

## 依赖

需要安装 PCSC 系统库：
```bash
# Ubuntu/Debian
sudo apt install pcscd libpcsclite-dev

# Arch Linux
sudo pacman -S pcsc-lite
```