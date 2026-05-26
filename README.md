# SmartcardAgent

智能卡知识库代理 - 一个基于 Tauri + React + Python 的桌面应用程序。

## 项目简介

SmartcardAgent 是一个智能卡知识库代理应用，帮助用户管理和查询智能卡相关的知识和数据。采用三层架构设计：

- **Tauri 桌面应用层**：Rust 后端，负责系统级调用和跨平台集成
- **React 前端层**：TypeScript/React，负责用户界面和交互
- **Python 知识库服务层**：独立进程，负责知识存储、检索和智能卡数据处理

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 桌面应用 | Tauri 2.x | 跨平台桌面应用框架，使用 Rust |
| 前端 | React 18 + TypeScript | 用户界面框架 |
| 构建工具 | Vite | 前端构建和开发服务器 |
| 后端服务 | Python 3.11+ | 知识库处理服务 |
| 包管理 | uv / pip | Python 包管理器 |

## 目录结构

```
smartcard-agent/
├── src-tauri/           # Tauri 应用（Rust）
│   ├── src/             # Rust 源码
│   ├── icons/           # 应用图标
│   ├── Cargo.toml       # Rust 依赖配置
│   └── tauri.conf.json  # Tauri 配置
├── src/                 # React 前端
│   ├── components/      # UI 组件
│   ├── pages/           # 页面
│   ├── hooks/           # React Hooks
│   ├── utils/           # 工具函数
│   ├── main.tsx         # 应用入口
│   └── App.tsx          # 根组件
├── python-service/      # Python 知识库服务
│   ├── src/             # Python 源码
│   │   ├── api/         # API 接口
│   │   ├── models/      # 数据模型
│   │   ├── services/    # 业务逻辑
│   │   ├── utils/       # 工具函数
│   │   └── main.py      # 服务入口
│   ├── tests/           # 测试
│   └── pyproject.toml   # Python 项目配置
├── index.html           # Vite 入口页面
├── package.json         # Node.js 依赖配置
├── tsconfig.json        # TypeScript 配置
├── vite.config.ts       # Vite 配置
└── .env.example         # 环境变量模板
```

## 开发指南

### 环境要求

- Node.js 18+
- Rust 1.70+
- Python 3.11+
- Tauri CLI

### 安装依赖

```bash
# 安装前端依赖
npm install

# 安装 Python 依赖
cd python-service
uv sync  # 或 pip install -e .
```

### 开发模式

```bash
# 1. 启动 Python 后端服务
cd python-service
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# 2. 启动 Tauri 桌面应用（前端 + Tauri）
npm run tauri:dev
```

**启动顺序**：先启动 Python 后端，再启动 Tauri 桌面应用。

### 构建

```bash
# 构建生产版本
npm run tauri build
```

### 代码质量检查

```bash
# 前端检查
npm run lint

# Python 检查
cd python-service
ruff check src/
```

## 参与贡献

1. Fork 本仓库
2. 新建 Feat_xxx 分支
3. 提交代码
4. 新建 Pull Request

## 许可证

MIT License