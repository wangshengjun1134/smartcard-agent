# Tauri App

Tauri 桌面应用框架规格。

## Requirements

### Requirement: Tauri 项目结构初始化

系统 SHALL 创建标准的 Tauri 项目目录结构，包含 `src-tauri/` 目录，内含 Rust 源码、配置和资源文件。

#### Scenario: 验证目录结构
- **WHEN** 检查项目根目录
- **THEN** 存在 `src-tauri/` 目录，包含 `src/`、`Cargo.toml`、`tauri.conf.json`

### Requirement: Tauri 配置文件完整

系统 SHALL 提供完整的 Tauri 配置文件，定义应用标识、窗口配置和安全策略。

#### Scenario: 验证配置文件
- **WHEN** 检查 `src-tauri/tauri.conf.json`
- **THEN** 文件包含 `productName`、`version`、`identifier`、`build`、`bundle` 配置节

### Requirement: Rust 依赖配置

系统 SHALL 在 `Cargo.toml` 中配置必要的 Rust 依赖，包括 Tauri 核心库和常用扩展。

#### Scenario: 验证依赖声明
- **WHEN** 检查 `src-tauri/Cargo.toml`
- **THEN** 文件包含 `tauri` 依赖声明

### Requirement: Python Sidecar 配置

系统 SHALL 在 Tauri 配置中声明 Python Sidecar，支持跨平台可执行文件打包。

#### Scenario: 验证 Sidecar 配置
- **WHEN** 检查 `src-tauri/tauri.conf.json` 的 `bundle.externalBin` 配置
- **THEN** 包含 Python 服务的 Sidecar 声明