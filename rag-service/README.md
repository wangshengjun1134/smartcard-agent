# RAG Service

知识库服务 - 文件管理与向量检索

## 功能

- 文件上传与管理（文件夹、移动）
- PDF 解析与章节分片（Docling）
- 向量存储与检索
- RAG 查询（检索增强生成）

## 运行

```bash
# 从项目根目录启动（使用统一的 .venv）
cd /home/buff/workspace/buff/smartcard-agent
source .venv/bin/activate
python -m uvicorn rag_service.main:app --port 8002 --reload
```

## API 端点

### 文件管理
- `GET /api/files/tree` - 获取文件树
- `POST /api/files/upload` - 上传文件
- `GET /api/files/{id}` - 获取文件详情
- `PUT /api/files/{id}` - 重命名文件
- `DELETE /api/files/{id}` - 删除文件
- `POST /api/files/folder` - 创建文件夹
- `POST /api/files/move` - 移动文件

### 文档管理
- `POST /api/documents/upload` - 上传文档
- `GET /api/documents/list` - 获取文档列表
- `GET /api/documents/{doc_id}` - 获取文档详情
- `PUT /api/documents/{doc_id}` - 更新文档
- `DELETE /api/documents/{doc_id}` - 删除文档

### 分片管理（Docling）
- `POST /api/chunks/parse-and-chunk` - 解析 PDF 并按章节分片
- `GET /api/chunks/by-document/{doc_id}` - 获取文档所有分片
- `GET /api/chunks/by-doc-heading` - 按章节标题获取分片
- `GET /api/chunks/by-page-range` - 按页码范围获取分片
- `GET /api/chunks/headings/{doc_id}` - 获取文档所有章节标题
- `DELETE /api/chunks/by-document/{doc_id}` - 删除文档所有分片

### 知识库
- `GET /api/knowledge-bases/list` - 获取知识库列表
- `POST /api/knowledge-bases` - 创建知识库
- `GET /api/knowledge-bases/{kb_id}` - 获取知识库详情
- `PUT /api/knowledge-bases/{kb_id}` - 更新知识库
- `DELETE /api/knowledge-bases/{kb_id}` - 删除知识库

### RAG 查询
- `POST /api/rag/add` - 添加知识
- `POST /api/rag/query` - RAG 查询
- `POST /api/rag/search` - 搜索文档
- `DELETE /api/rag/collection` - 删除向量集合

### 其他
- `GET /health` - 健康检查

## 数据目录

- `data/docs/` - 文件存储
- `data/qdrant/` - 向量数据库
- `data/models/bge-m3/` - Embedding 模型
- `data/models/docling/` - Docling 解析模型
- `data/knowledge.db` - 文件元数据库
