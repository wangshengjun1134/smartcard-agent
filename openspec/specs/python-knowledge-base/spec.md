# Python Knowledge Base

Python 知识库服务规格。

## Requirements

### Requirement: Python 项目结构初始化

系统 SHALL 创建标准的 Python 项目目录结构，包含 `python-service/` 目录，内含源码、配置和测试模块。

#### Scenario: 验证目录结构
- **WHEN** 检查项目根目录
- **THEN** 存在 `python-service/` 目录，包含 `src/`、`tests/`、`pyproject.toml`

### Requirement: Python 包管理配置

系统 SHALL 使用 `pyproject.toml` 配置项目依赖和构建信息，符合现代 Python 打包标准。

#### Scenario: 验证 pyproject.toml
- **WHEN** 检查 `python-service/pyproject.toml`
- **THEN** 文件包含 `[project]`、`[build-system]` 配置节

### Requirement: 核心模块结构

系统 SHALL 创建清晰的核心模块结构，分离 API、模型和业务逻辑。

#### Scenario: 验证模块结构
- **WHEN** 检查 `python-service/src/` 目录
- **THEN** 包含 `api/`、`agents/`、`skills/`、`apdu/`、`tools/`、`runtime/`、`models/`、`services/`、`llm/`、`vectordb/`、`utils/` 子目录和 `__init__.py`

### Requirement: Tauri Sidecar 入口

系统 SHALL 提供可被 Tauri Sidecar 调用的入口点，支持 stdio 或 HTTP 通信。

#### Scenario: 验证入口点
- **WHEN** 检查 `python-service/src/main.py`
- **THEN** 文件存在且包含可执行入口函数

### Requirement: 代码质量工具

系统 SHALL 配置 Black、isort 和 Ruff，确保 Python 代码风格一致性。

#### Scenario: 验证格式化工具配置
- **WHEN** 检查 `python-service/pyproject.toml` 的工具配置
- **THEN** 包含 `[tool.black]`、`[tool.isort]`、`[tool.ruff]` 配置

### Requirement: Agent API 接口

系统 SHALL 新增 Agent 对话 API 接口 `/api/agent/chat`，接收用户输入返回 Agent 响应。

#### Scenario: Agent 对话请求
- **WHEN** POST /api/agent/chat body = {"message": "读取 IMSI"}
- **THEN** 返回 Agent 响应包含执行结果或知识库答案

### Requirement: Agent 模块依赖

系统 SHALL 在 pyproject.toml 新增依赖：langgraph, pyscard, pydantic。

#### Scenario: 验证新增依赖
- **WHEN** 检查 pyproject.toml dependencies
- **THEN** 包含 langgraph, pyscard, pydantic