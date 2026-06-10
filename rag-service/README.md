# RAG Service

知识库服务 - 文件管理与向量检索

## 功能

- 文件上传与管理（文件夹、移动）
- 向量存储与检索
- RAG 查询（检索增强生成）

## 运行

```bash
# 安装依赖
pip install -e .

# 运行服务（在 rag-service 目录下）
python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8002 --reload
```

## API 端点

- `GET /api/files/tree` - 获取文件树
- `POST /api/files/upload` - 上传文件
- `POST /api/rag/query` - RAG 查询
- `POST /api/rag/search` - 搜索文档
- `GET /health` - 健康检查

## 数据目录

- `data/docs/` - 文件存储
- `data/qdrant/` - 向量数据库
- `data/models/bge-m3/` - Embedding 模型
- `data/knowledge.db` - 文件元数据库