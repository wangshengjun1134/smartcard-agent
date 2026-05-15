# Project Config

项目配置管理规格。

## Requirements

### Requirement: 根级项目配置

系统 SHALL 在项目根目录提供统一的项目配置文件，包括 README、.gitignore 和开发文档。

#### Scenario: 验证根级文件
- **WHEN** 检查项目根目录
- **THEN** 存在 `README.md`、`.gitignore` 文件

### Requirement: README 文档

系统 SHALL 提供完整的 README 文档，说明项目结构、技术栈、开发指南和构建步骤。

#### Scenario: 验证 README 内容
- **WHEN** 检查 `README.md` 内容
- **THEN** 包含项目简介、技术栈说明、目录结构、开发指南

### Requirement: Git 忽略配置

系统 SHALL 配置 `.gitignore`，排除编译产物、依赖目录、IDE 配置和系统文件。

#### Scenario: 验证 gitignore 规则
- **WHEN** 检查 `.gitignore` 内容
- **THEN** 包含 `node_modules/`、`target/`、`__pycache__/`、`*.log`、`.env` 规则

### Requirement: 跨项目脚本

系统 SHALL 提供统一的构建和开发脚本，简化跨技术栈操作。

#### Scenario: 验证 npm scripts
- **WHEN** 检查根目录 `package.json` 的 scripts
- **THEN** 包含 `dev`、`build`、`test` 脚本命令

### Requirement: 环境配置模板

系统 SHALL 提供环境变量配置模板文件，说明必需的配置项。

#### Scenario: 验证环境配置模板
- **WHEN** 检查 `.env.example` 文件
- **THEN** 文件存在且包含配置项说明