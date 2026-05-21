## ADDED Requirements

### Requirement: Runtime Context 结构

系统 SHALL 实现 RuntimeContext 类，管理 connected, current_reader, atr, selected_path, current_application, pin_verified, secure_channel_state, card_capabilities, discovered_apps, execution_history 字段。

#### Scenario: 验证 Context 结构
- **WHEN** 检查 `runtime/context.py`
- **THEN** RuntimeContext 包含所有状态字段和更新方法

### Requirement: Checkpoint Manager

系统 SHALL 实现 Checkpoint Manager，支持 save_checkpoint, restore_checkpoint, replay_execution, rollback_state 操作。

#### Scenario: 保存执行检查点
- **WHEN** 执行关键 Skill 前
- **THEN** Checkpoint Manager 记录当前 runtime_state 和 execution_history

#### Scenario: 恢复检查点
- **WHEN** APDU 执行失败需要重试
- **THEN** restore_checkpoint 恢复到上一检查点状态

### Requirement: Retry Engine

系统 SHALL 实现 Retry Engine，检测 retryable_error，执行 reconnect_and_resume，应用 retry_policy。

#### Scenario: 检测可重试错误
- **WHEN** SW = "6F00" 或连接丢失
- **THEN** Retry Engine 返回 is_retryable = True

#### Scenario: 重试策略应用
- **WHEN** 重试次数 < max_retries
- **THEN** 执行 reconnect_and_resume，恢复 selected_path 后重新执行

### Requirement: Retry Policy 配置

系统 SHALL 支持 retry_policy 配置：max_retries, retry_delay, retryable_errors 列表。

#### Scenario: 验证策略配置
- **WHEN** 检查 `runtime/retry_policy.py`
- **THEN** RetryPolicy 类包含 max_retries, retry_delay 配置