# RAG Service

知识库服务 — 提供文件管理、PDF 解析、文档分片、向量存储与 RAG 检索增强生成功能。

## 架构概览

```
rag-service/
├── rag_service/
│   ├── main.py                  # FastAPI 入口 (port 8002)
│   ├── api/                     # API 路由层
│   │   ├── files.py             # 文件树 / 上传 / 重命名 / 移动 / 删除
│   │   ├── documents.py         # 文档 CRUD (含知识库关联)
│   │   ├── knowledge_bases.py   # 知识库 CRUD
│   │   ├── chunks.py            # PDF 解析、分片、向量化端点
│   │   └── rag.py               # RAG 查询 / 相似度搜索
│   ├── services/                # 业务逻辑层
│   │   ├── file_service.py      # 文件树、上传、移动、重命名、删除 (软删除)
│   │   ├── document_service.py  # 文档 CRUD、状态追踪、友好路径解析
│   │   ├── chunk_service.py     # 分片 CRUD、待处理查询、批量操作
│   │   ├── docling_chunker.py   # Docling PDF 解析 + 层级分片
│   │   ├── embedding_service.py # 批量向量化到 Qdrant、状态追踪
│   │   ├── knowledge_base_service.py  # 知识库 CRUD (级联删除)
│   │   ├── processing_log_service.py  # 处理日志 CRUD (审计追踪)
│   │   └── rag_service.py       # RAG 链 (检索 + LLM 生成)
│   ├── models/                  # Pydantic 数据模型
│   │   ├── file.py              # FileRecord, FileNode, FileDetail
│   │   ├── document.py          # DocumentRecord, DocumentResponse, 状态枚举
│   │   ├── chunk.py             # ChunkRecord, ChunkResponse (含标题/页码追踪)
│   │   ├── knowledge_base.py    # KnowledgeBaseRecord/Response
│   │   ├── processing_log.py    # ProcessingLogRecord (解析/分片/向量化操作)
│   │   └── embedding.py         # Embedding 配置与工厂
│   ├── llm/                     # LLM 与 Embedding 模块
│   │   ├── config.py            # LLMConfig (数据库缓存, 5 分钟 TTL)
│   │   ├── llm.py               # ChatOpenAI 工厂 + 日志回调
│   │   ├── embeddings.py        # Embeddings 工厂 (含缓存)
│   │   └── local_embeddings.py  # BGE-m3 本地 Embedding (sentence-transformers)
│   ├── vectordb/                # 向量数据库
│   │   ├── config.py            # VectorDBConfig (Qdrant 连接配置)
│   │   └── qdrant_store.py      # QdrantStore 封装 (添加/搜索/删除)
│   ├── utils/database.py        # SQLite 工具 (WAL 模式, 建表, 种子数据)
│   └── smartcard_knowledge_base/
│       └── __init__.py          # 包标记
├── tests/                       # PDF 解析测试
│   ├── test_docling_pdf.py      # Docling PDF 解析 + 分片测试
│   ├── test_unstructured_pdf.py # Unstructured PDF 解析测试
│   └── GPC_Specification_v2.3*.pdf  # 测试用 PDF 样本
├── data/                        # 运行时数据 (git-ignored)
│   ├── docs/                    # 文件存储
│   ├── qdrant/                  # Qdrant 向量数据
│   ├── models/
│   │   ├── bge-m3/              # BGE-m3 Embedding 模型
│   │   └── docling/             # Docling 解析模型
│   └── knowledge.db             # SQLite 元数据库
└── pyproject.toml
```

## 核心功能

### PDF 解析与分片

使用 **Docling** 进行 PDF 解析，支持布局分析、表格识别、OCR（默认关闭）：

1. **阅读顺序遍历**: 按文档元素顺序迭代
2. **标题栈维护**: 维护标题栈，遇到新标题时弹出深层/同级标题并压入新标题
3. **标题路径构建**: 用 ` > ` 连接栈内标题 (如 `1 Introduction > 1.1 Audience`)
4. **标题层级估算**: 解析编号模式 (1.1.2 → level 3, A. → level 1, 罗马数字 → level 1)
5. **章节聚合**: 将文本项归入当前标题路径，追踪页码
6. **大小控制**: 章节超过 `MAX_CHUNK_CHARS` (4000) 时进行二次分割，重叠 `OVERLAP_CHARS` (200)
7. **子分片命名**: 重叠子分片命名为 `1 Intro (part 2)` 格式

每个分片记录: `heading`, `heading_level`, `page_start`, `page_end`, `overlap`, `is_subchunk`。

### 向量存储

- **引擎**: Qdrant (qdrant-client 嵌入式模式)
- **集合**: `smartcard_knowledge` (可通过 `VECTOR_DB_COLLECTION` 配置)
- **向量维度**: 1024 (BGE-m3)
- **距离度量**: COSINE
- **存储位置**: `data/qdrant/`

### Embedding 模型

- **默认模型**: BAAI/bge-m3 (本地加载, 通过 sentence-transformers)
- **模型路径**: `data/models/bge-m3/` (自动从 HuggingFace 下载)
- **缓存**: 全局单例，服务启动时预加载

### RAG 查询

基于 LangChain 的 RAG 链：
1. **检索**: 从 Qdrant 检索相似文档
2. **格式化**: 将检索结果格式化为上下文
3. **生成**: 使用 LLM (qwen3.5-plus) 生成回答

## 运行

```bash
# 从项目根目录操作
cd /home/buff/workspace/buff/smartcard-agent
source .venv/bin/activate

# 安装依赖
pip install -e rag-service/

# 运行服务
python -m uvicorn rag_service.main:app --port 8002 --reload
```

## API 端点

### 文件管理 (`/api/files`)

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/tree` | 获取完整文件树 |
| `POST` | `/upload` | 上传文件 (100MB 限制) |
| `GET` | `/{file_id}` | 获取文件详情 |
| `PUT` | `/{file_id}/rename` | 重命名文件/文件夹 |
| `DELETE` | `/{file_id}` | 软删除文件 |
| `POST` | `/folder` | 创建文件夹 |
| `POST` | `/move` | 移动文件/文件夹 (含路径前缀更新) |

### 文档管理 (`/api/documents`)

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/upload` | 上传文档到知识库 (SHA-256 哈希, MIME 检测) |
| `GET` | `/list` | 列出文档 (支持 kb_id/状态过滤, 分页) |
| `GET` | `/{doc_id}` | 获取文档详情 |
| `PUT` | `/{doc_id}` | 更新文档元数据 |
| `DELETE` | `/{doc_id}` | 软删除文档 (is_active = 0) |

### 分片管理 (`/api/chunks`)

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/parse-and-chunk` | 解析 PDF + 分片 + 可选自动向量化 (后台任务) |
| `POST` | `/embed` | 启动待分片向量化 (后台任务) |
| `GET` | `/by-document/{doc_id}` | 获取文档所有分片 |
| `GET` | `/by-doc-heading` | 按标题前缀匹配获取分片 |
| `GET` | `/by-page-range` | 按页码范围获取分片 |
| `GET` | `/headings/{doc_id}` | 获取文档所有标题列表 |
| `DELETE` | `/by-document/{doc_id}` | 删除文档所有分片 |

### 知识库 (`/api/knowledge-bases`)

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/list` | 列出所有知识库 |
| `POST` | `/` | 创建知识库 (名称唯一约束) |
| `GET` | `/{kb_id}` | 获取知识库详情 |
| `PUT` | `/{kb_id}` | 更新知识库 |
| `DELETE` | `/{kb_id}` | 删除知识库 (级联: 文档, 分片, 日志) |

### RAG 查询 (`/api/rag`)

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/add` | 添加文本知识到向量库 |
| `POST` | `/query` | RAG 查询 (返回 LLM 生成答案) |
| `POST` | `/search` | 相似度搜索 (返回文档 + 分数) |
| `DELETE` | `/collection` | 删除整个向量集合 |
| `GET` | `/info` | 集合统计信息 |

### 其他

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |

## 数据库

SQLite 数据库位于 `data/knowledge.db`，包含以下表：

| 表 | 说明 |
|----|------|
| `files` | 文件树层级 (文件夹/文件, 软删除) |
| `knowledge_bases` | 知识库 (唯一名称约束, 含种子数据) |
| `documents` | 文档元数据 (关联知识库和文件夹, 含状态追踪) |
| `chunks` | 文档分片 (含标题路径、页码、向量化状态) |
| `processing_logs` | 处理日志 (解析/分片/向量化操作的审计追踪) |

启用 WAL 模式。

## 配置

通过 `.env` 文件配置 (见 `.env.example`)，使用 Pydantic Settings 加载 (`extra="ignore"`)：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | - | LLM API 密钥 |
| `LLM_BASE_URL` | https://dashscope.aliyuncs.com/compatible-mode/v1 | LLM API 地址 |
| `LLM_MODEL_NAME` | qwen3.5-plus | 默认模型 |
| `EMBEDDING_MODEL_PATH` | ./data/models/bge-m3 | BGE-m3 模型路径 |
| `EMBEDDING_DEVICE` | cpu | Embedding 设备 |
| `QDRANT_HOST` | localhost | Qdrant 主机 |
| `QDRANT_PORT` | 6333 | Qdrant 端口 |
| `QDRANT_COLLECTION` | smartcard_knowledge | Qdrant 集合名 |
| `STORAGE_PATH` | ./data/docs | 文件存储路径 |
| `KNOWLEDGE_DB_PATH` | ./data/knowledge.db | 元数据库路径 |
| `API_PORT` | 8002 | 服务端口 |

## 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **LLM 交互**: LangChain + OpenAI SDK
- **PDF 解析**: Docling (布局分析, 表格识别, OCR 可选)
- **向量数据库**: Qdrant (qdrant-client 嵌入式)
- **Embedding**: sentence-transformers (BGE-m3)
- **数据模型**: Pydantic + Pydantic Settings
- **数据库**: SQLite (WAL 模式)
