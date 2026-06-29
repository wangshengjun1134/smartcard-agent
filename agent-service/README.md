# Agent Service

智能卡操作 Agent 服务 — 提供 LLM 驱动的推理循环、智能卡 PC/SC 操作、会话管理和插件化技能系统。

## 架构概览

```
agent-service/
├── agent_service/
│   ├── main.py                  # FastAPI 入口 (port 8001)
│   ├── api/                     # API 路由层
│   │   ├── agent.py             # Agent 聊天 (SSE 流式 + 非流式)
│   │   ├── session.py           # 会话/分组/消息 CRUD
│   │   ├── smartcard.py         # PC/SC 读卡器 & APDU 操作
│   │   ├── events.py            # WebSocket APDU 事件广播
│   │   └── config.py            # LLM API 配置管理
│   ├── agents/                  # Agent 核心
│   │   ├── core/
│   │   │   ├── agent_core.py    # 推理循环: stream → tool_calls → execute → repeat
│   │   │   ├── tool_scheduler.py# 工具注册与执行调度器
│   │   │   ├── message.py       # 消息数据类与构建器
│   │   │   └── events.py        # SSE 事件发射工具
│   │   ├── graph/workflow.py    # 工作流编排 (AgentCore 封装, SSE 流式)
│   │   └── tools/builtin.py     # 内置工具注册 (send_apdu, ask_user, skill 包装)
│   ├── skills/                  # 技能插件系统
│   │   ├── base/
│   │   │   ├── base_skill.py    # BaseSkill 抽象类 + SkillResult
│   │   │   ├── metadata.py      # SkillMetadata (分类, 安全级别, 参数 schema)
│   │   │   └── registry.py      # SkillRegistry (注册/查找/验证)
│   │   └── registry_extension.py# 动态插件发现 (.skills/, external_skills/, SKILL_DIRS)
│   ├── tools/pcsc/              # PC/SC 客户端
│   │   ├── client.py            # PcscClient (pyscard 封装)
│   │   └── exceptions.py        # PC/SC 异常体系
│   ├── runtime/                 # 运行时上下文
│   │   ├── context.py           # RuntimeContext (连接状态, PC/SC 客户端, 事件监听)
│   │   ├── checkpoint.py        # CheckpointManager (状态保存/恢复)
│   │   └── retry_policy.py      # 重试策略与引擎
│   ├── llm/                     # LLM 模块
│   │   ├── llm.py               # LLM 工厂 (ChatOpenAI + AsyncOpenAI)
│   │   └── config.py            # LLMConfig (数据库驱动, 5 分钟缓存)
│   ├── apdu/                    # APDU 工具集
│   │   ├── builders/            # APDU 命令构建器 (SELECT, READ, AUTH)
│   │   ├── parsers/             # BER-TLV / Status Word / FCP 解析器
│   │   └── constants/           # ISO 7816 常量 (SW 码, 指令, 文件 ID)
│   ├── dsl/compiler.py          # APDSL 编译器 (预定义 APDU 序列 DSL)
│   ├── models/                  # Pydantic 数据模型
│   └── utils/database.py        # SQLite 工具 (会话/消息/api_config 表)
├── .skills/                     # 技能插件目录
├── data/                        # 运行时数据 (git-ignored)
│   └── message.db               # SQLite 会话/消息数据库
└── pyproject.toml
```

## 核心功能

### Agent 推理循环

Agent 使用两阶段推理循环处理用户请求：

1. **流式阶段**: 使用 `AsyncOpenAI` 流式输出 LLM 响应，实时展示思考过程
2. **工具调用**: 检测 tool_calls，通过 `ToolScheduler` 执行对应工具
3. **循环迭代**: 将工具结果反馈给 LLM，直到产出纯文本响应或达到最大迭代次数

### 技能插件系统

技能以插件形式动态加载，支持三类发现路径：
- `.skills/` — 内置技能目录
- `external_skills/` — 外部技能目录
- `SKILL_DIRS` — 环境变量指定的额外路径

每个技能由 `skill.md` (YAML frontmatter 元数据) + `__init__.py` (含 `register()` 函数) 组成。

### PC/SC 智能卡操作

- 读卡器列表查询与连接状态检测
- T0/T1 协议连接与 ATR 获取
- APDU 命令发送 (hex 字符串或 bytes)
- 批量 APDU 序列执行 (通过 `apdus` 参数)
- APDU 事件通过 WebSocket 实时广播到前端

### APDU 命令构建

使用 Builder 模式生成标准 APDU 命令：
- **SelectBuilder**: SELECT FILE / SELECT by AID
- **ReadBuilder**: READ BINARY / READ RECORD
- **AuthBuilder**: VERIFY PIN / CHANGE PIN / GET CHALLENGE

### APDSL 领域特定语言

APDSL 是一种用于定义预定义 APDU 序列的文本 DSL（如 `read_imsi`, `read_iccid`），编译器将脚本解析为可执行序列。

## 运行

```bash
# 从项目根目录操作
cd /home/buff/workspace/buff/smartcard-agent
source .venv/bin/activate

# 安装依赖
pip install -e agent-service/

# 运行服务
python -m uvicorn agent_service.main:app --port 8001 --reload
```

### 系统依赖

需要安装 PC/SC 系统库：

```bash
# Ubuntu/Debian
sudo apt install pcscd libpcsclite-dev

# Arch Linux
sudo pacman -S pcsc-lite
```

确保 `pcscd` 服务已启动：

```bash
sudo systemctl start pcscd
```

## API 端点

### Agent 聊天

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/agent/chat` | Agent 聊天 (非流式) |
| `POST` | `/api/agent/chat/stream` | Agent 聊天 (SSE 流式) |
| `GET` | `/api/agent/status` | Agent 状态 |
| `GET` | `/api/agent/skills` | 列出所有已注册技能 |
| `GET` | `/api/agent/skills/{name}` | 获取指定技能详情 |

SSE 流式事件类型: `thinking`, `thinking_chunk`, `tool_call`, `tool_result`, `content`, `done`

### 会话管理

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/session/list` | 列出所有会话 |
| `POST` | `/api/session/create` | 创建新会话 |
| `GET` | `/api/session/{id}` | 获取会话及所有消息 |
| `PUT` | `/api/session/{id}` | 更新会话 (标题, 分组, 置顶) |
| `DELETE` | `/api/session/{id}` | 删除会话 (级联删除消息) |
| `GET` | `/api/session/groups` | 列出会话分组 |
| `POST` | `/api/session/groups` | 创建会话分组 |
| `PUT` | `/api/session/groups/{id}` | 更新会话分组 |
| `DELETE` | `/api/session/groups/{id}` | 删除会话分组 (级联删除会话) |
| `GET` | `/api/session/{id}/messages` | 列出会话消息 |
| `POST` | `/api/session/{id}/messages` | 添加消息到会话 |

### 智能卡操作

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/smartcard/readers` | 列出可用读卡器及连接状态 |
| `POST` | `/api/smartcard/connect` | 连接到指定读卡器 (返回 ATR) |
| `POST` | `/api/smartcard/disconnect` | 断开读卡器连接 |
| `POST` | `/api/smartcard/apdu` | 发送 APDU 命令 (hex 字符串) |
| `WS` | `/ws/apdu` | WebSocket APDU 事件实时广播 |

### LLM 配置

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/config/api` | 获取当前 LLM API 配置 |
| `POST` | `/api/config/api` | 保存/更新 LLM API 配置 |
| `POST` | `/api/config/api/test` | 测试 LLM API 连接 (返回延迟) |

### 其他

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |

## 数据库

SQLite 数据库位于 `data/message.db`，包含以下表：

| 表 | 说明 |
|----|------|
| `session_groups` | 会话分组 |
| `sessions` | 会话 (外键关联分组) |
| `messages` | 消息 (role: user/assistant/tool, 含 thinking_process/thinking_content) |
| `api_config` | LLM API 配置 (provider, base_url, api_key, model) |

启用 WAL 模式，索引覆盖 `sessions.group_id`, `sessions.updated_at`, `messages.session_id`。

## 配置

通过 `.env` 文件配置 (见 `.env.example`)，使用 Pydantic Settings 加载 (`extra="ignore"`)：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | - | LLM API 密钥 |
| `LLM_BASE_URL` | https://dashscope.aliyuncs.com/compatible-mode/v1 | LLM API 地址 |
| `LLM_MODEL_NAME` | qwen3.5-plus | 默认模型 |
| `AGENT_MAX_ITERATIONS` | 20 | 最大推理迭代次数 |
| `AGENT_MAX_TURNS` | 15 | 最大工具调用轮次 |
| `AGENT_MAX_TIME_MINUTES` | 10 | 最大执行时间 (分钟) |
| `PCSC_READER_INDEX` | 0 | 默认读卡器索引 |
| `API_PORT` | 8001 | 服务端口 |
| `SESSION_DB_PATH` | ./data/message.db | 数据库路径 |
| `SKILLS_DIR` | ./.skills | 技能插件目录 |

## 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **LLM 交互**: LangChain + OpenAI SDK (AsyncOpenAI)
- **智能卡**: pyscard (PC/SC 封装)
- **数据模型**: Pydantic + Pydantic Settings
- **数据库**: SQLite (WAL 模式)
