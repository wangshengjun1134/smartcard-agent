# SmartcardAgent

智能卡知识库代理 — 基于 Tauri + React + Python 的桌面应用程序，提供智能卡操作、知识库管理和 RAG 检索增强生成。

## 项目简介

SmartcardAgent 是一个智能卡知识库代理应用，帮助用户管理和查询智能卡相关的知识和数据。应用采用三层架构：

- **Tauri 桌面应用层**: Rust 后端，负责系统级调用和跨平台集成
- **React 前端层**: TypeScript/React，负责用户界面和交互
- **Python 服务层**: 独立进程，提供智能卡操作 (Agent Service) 和知识库管理 (RAG Service)

## 架构

```
smartcard-agent/
├── src-tauri/                 # Tauri 桌面应用 (Rust)
│   ├── src/                   # Rust 源码
│   ├── capabilities/          # Tauri 权限配置
│   ├── icons/                 # 应用图标
│   ├── Cargo.toml             # Rust 依赖
│   └── tauri.conf.json        # Tauri 配置
├── src/                       # React 前端 (TypeScript)
│   ├── components/            # UI 组件
│   ├── pages/                 # 页面组件
│   ├── hooks/                 # React Hooks
│   ├── utils/                 # 工具函数
│   ├── main.tsx               # 应用入口
│   └── App.tsx                # 根组件
├── agent-service/             # Agent 服务 (端口 8001)
│   ├── agent_service/         # Python 源码包
│   │   ├── api/               # API 路由 (Agent, Session, Smartcard, WebSocket)
│   │   ├── agents/            # Agent 核心 (推理循环, 工具调度, 工作流)
│   │   ├── skills/            # 技能插件系统 (BaseSkill, Registry, 动态发现)
│   │   ├── tools/pcsc/        # PC/SC 客户端 (pyscard 封装)
│   │   ├── runtime/           # 运行时上下文 (连接状态, 检查点, 重试)
│   │   ├── llm/               # LLM 模块 (ChatOpenAI, AsyncOpenAI)
│   │   ├── apdu/              # APDU 工具 (构建器, 解析器, 常量)
│   │   ├── dsl/               # APDSL 编译器 (预定义 APDU 序列)
│   │   └── models/            # Pydantic 数据模型
│   ├── .skills/               # 技能插件目录
│   ├── data/                  # 运行时数据 (message.db, checkpoints)
│   └── pyproject.toml
├── rag-service/               # RAG 服务 (端口 8002)
│   ├── rag_service/           # Python 源码包
│   │   ├── api/               # API 路由 (Files, Documents, Chunks, KB, RAG)
│   │   ├── services/          # 业务逻辑 (文件, 文档, 分片, Embedding, RAG)
│   │   ├── models/            # Pydantic 数据模型
│   │   ├── llm/               # LLM & Embedding 模块
│   │   ├── vectordb/          # Qdrant 向量数据库
│   │   └── utils/             # 数据库工具
│   ├── tests/                 # PDF 解析测试
│   ├── data/                  # 运行时数据 (docs, qdrant, models, knowledge.db)
│   └── pyproject.toml
├── .venv/                     # 统一 Python 虚拟环境
├── index.html                 # Vite 入口页面
├── package.json               # Node.js 依赖
├── tsconfig.json              # TypeScript 配置
├── vite.config.ts             # Vite 配置
├── tailwind.config.js         # Tailwind CSS 配置
└── .env.example               # 环境变量模板
```

## 服务架构

```
┌─────────────────────────────────────────────────┐
│              Tauri 桌面应用                       │
│  ┌─────────────────┐    ┌─────────────────────┐  │
│  │   Rust Backend   │    │   React Frontend    │  │
│  │  (系统调用/集成)  │◄──►│  (TypeScript/React) │  │
│  └─────────────────┘    └─────────┬───────────┘  │
└───────────────────────────────────┼──────────────┘
                                    │ HTTP / WebSocket
                    ┌───────────────┴───────────────┐
                    │                               │
        ┌───────────▼───────────┐   ┌──────────────▼────────────┐
        │    Agent Service      │   │      RAG Service          │
        │    (port 8001)        │   │      (port 8002)          │
        │                       │   │                           │
        │  • LLM 推理循环        │   │  • 文件管理                │
        │  • 技能插件系统        │   │  • PDF 解析 & 分片         │
        │  • PC/SC 智能卡操作    │   │  • Qdrant 向量存储         │
        │  • APDU 构建/解析      │   │  • BGE-m3 Embedding       │
        │  • 会话管理            │   │  • RAG 检索增强生成        │
        │  • WebSocket 事件广播  │   │  • 知识库 CRUD             │
        └───────────────────────┘   └───────────────────────────┘
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 桌面应用 | Tauri 2.x | 跨平台桌面框架 (Rust) |
| 前端 | React 18 + TypeScript | UI 框架 |
| 样式 | Tailwind CSS | 原子化 CSS |
| 构建 | Vite | 前端构建工具 |
| Agent 服务 | Python 3.11+ | FastAPI + LangChain + pyscard |
| RAG 服务 | Python 3.11+ | FastAPI + LangChain + Qdrant + Docling |
| LLM | qwen3.5-plus | 通过 DashScope API |
| Embedding | BGE-m3 | 本地 1024 维向量 |
| 向量库 | Qdrant | 嵌入式模式 |
| 数据库 | SQLite | WAL 模式 |

## 开发指南

### 环境要求

- Node.js 18+
- Rust 1.70+
- Python 3.11+
- Tauri CLI
- PC/SC 系统库 (`pcscd`, `libpcsclite-dev`)

### 安装依赖

```bash
# 前端依赖
npm install

# Python 虚拟环境 (项目根目录统一 .venv)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# 安装 Python 服务
pip install -e agent-service/
pip install -e rag-service/
```

### 开发模式

```bash
# 激活虚拟环境
source .venv/bin/activate

# 1. Agent 服务 (智能卡操作, 端口 8001)
python -m uvicorn agent_service.main:app --port 8001 --reload

# 2. RAG 服务 (知识库, 端口 8002)
python -m uvicorn rag_service.main:app --port 8002 --reload

# 3. Tauri 桌面应用 (另一个终端)
npm run tauri:dev
```

**启动顺序**: 先启动 Python 后端服务，再启动 Tauri 桌面应用。

### 构建

```bash
# 构建生产版本
npm run tauri build
```

### 代码质量

```bash
# 前端检查
npm run lint

# Python 检查 (从项目根目录)
ruff check agent-service/rag-service/
```

## Agent 服务详解

### 推理循环

Agent 使用两阶段推理循环：
1. **流式输出**: 实时展示 LLM 思考过程 (`thinking`, `thinking_chunk` 事件)
2. **工具调用**: 检测 tool_calls → ToolScheduler 执行 → 结果反馈 → 循环
3. **终止条件**: 产出纯文本 / 达到最大迭代次数 / 超时

SSE 事件类型: `thinking`, `thinking_chunk`, `tool_call`, `tool_result`, `content`, `done`

### 技能插件系统

技能以插件形式动态加载，支持三类发现路径：
- `.skills/` — 内置技能目录
- `external_skills/` — 外部技能目录
- `SKILL_DIRS` — 环境变量指定的额外路径

每个技能由 `skill.md` (YAML 元数据) + `__init__.py` (含 `register()` 函数) 组成。

### PC/SC 智能卡操作

- 读卡器列表查询与连接状态检测
- T0/T1 协议连接与 ATR 获取
- APDU 命令发送 (hex 或 bytes)
- 批量 APDU 序列执行
- WebSocket 实时事件广播到前端 APDU 控制台

## RAG 服务详解

### PDF 解析与分片

使用 **Docling** 进行 PDF 解析：
1. 阅读顺序遍历 + 标题栈维护
2. 标题路径构建 (` > ` 分隔符)
3. 层级估算 + 章节聚合
4. 大小控制 (4000 字符限制, 200 字符重叠)
5. 子分片命名 (`(part N)` 格式)

### 向量检索

- **引擎**: Qdrant 嵌入式模式
- **集合**: `smartcard_knowledge`
- **维度**: 1024 (BGE-m3)
- **距离**: COSINE

### RAG 查询

LangChain RAG 链: 检索 → 格式化 → LLM 生成 (qwen3.5-plus)

## 数据目录

项目根目录下的 `data/` 目录用于存放所有运行时数据，已被 `.gitignore` 排除（模型文件体积较大，约 34GB）。

```
data/
├── models/                    # AI 模型（不提交到 git）
│   ├── bge-m3/                # BGE-m3 Embedding 模型 (~2GB)
│   ├── docling/               # Docling PDF 解析模型 (~30GB+)
│   │   ├── docling-layout-heron/          # 版面分析模型（必需）
│   │   ├── docling-models/                # TableFormer 表格识别
│   │   ├── CodeFormulaV2/                 # 代码/公式识别（可选）
│   │   ├── granite-docling-258M/          # Granite Docling 模型
│   │   └── ...                            # 其他可选模型
│   └── yolo_x_layout/         # YOLOX 版面分析模型 (~500MB)
├── docs/                      # 用户上传的知识库文件
│   └── GP规范/
│       └── GPC_Specification_v2.3.pdf
├── qdrant/                    # Qdrant 向量数据库 (~2MB)
├── message.db                 # Agent 服务会话/消息数据库 (~636KB)
├── knowledge.db               # RAG 服务元数据库 (~412KB)
└── session.db                 # 旧版会话数据库 (~48KB)
```

> **注意**: `data/` 目录下的模型文件体积较大（总计约 34GB），首次运行服务时会自动从 HuggingFace 下载所需模型。
> 国内网络可使用镜像站加速，详见各服务的 README 中模型配置说明。

## 配置

通过 `.env` 文件配置，复制 `.env.example` 并修改：

```bash
cp .env.example .env
```

两个服务共享 `.env` 文件，各自通过 Pydantic Settings 提取所需字段 (`extra="ignore"`)。

详见各服务的 README:
- [Agent Service 配置](agent-service/README.md#配置)
- [RAG Service 配置](rag-service/README.md#配置)

## 参与贡献

1. Fork 本仓库
2. 新建 Feat_xxx 分支
3. 提交代码
4. 新建 Pull Request

## 许可证

MIT License
