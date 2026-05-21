## ADDED Requirements

### Requirement: Skill 基类设计

系统 SHALL 实现 BaseSkill 基类，定义 name, description, dangerous, requires_pin, requires_secure_channel 元数据和 run(ctx, params) 方法。

#### Scenario: 验证基类结构
- **WHEN** 检查 `skills/base/base_skill.py`
- **THEN** BaseSkill 类包含所有元数据属性和 run 方法签名

### Requirement: Skill Registry

系统 SHALL 实现 Skill Registry，支持 register(skill) 注册和 get_skill(name) 查询。

#### Scenario: 注册和查询 Skill
- **WHEN** 调用 register(SelectFileSkill) 后调用 get_skill("select_file")
- **THEN** 返回已注册的 SelectFileSkill 实例

### Requirement: Primitive Skills

系统 SHALL 实现 Primitive Skills：select_file, read_binary, read_record, verify_pin, get_response, authenticate。

#### Scenario: 执行 select_file Skill
- **WHEN** 执行 select_file skill 参数 fid = "3F00"
- **THEN** 构建 SELECT APDU 并发送，更新 runtime_state.selected_path

### Requirement: Composite Skills

系统 SHALL 实现 Composite Skills：read_imsi, read_iccid, read_msisdn, read_spn, usim_authenticate。

#### Scenario: 执行 read_imsi Skill
- **WHEN** 执行 read_imsi skill
- **THEN** 自动执行 select_file(3F00) → select_file(7F20) → select_file(6F07) → read_binary

### Requirement: Exploratory Skills

系统 SHALL 实现 Exploratory Skills：discover_card, detect_applications, detect_secure_channel, scan_filesystem, probe_capabilities。

#### Scenario: 执行 discover_card Skill
- **WHEN** 执行 discover_card skill
- **THEN** 读取 ATR，分析卡类型，更新 runtime_state.card_capabilities

### Requirement: Skill Metadata 安全控制

系统 SHALL 检查 Skill Metadata，dangerous/requires_pin/requires_secure_channel 标记触发安全提示或前置条件验证。

#### Scenario: 验证危险 Skill
- **WHEN** 执行 dangerous = True 的 Skill
- **THEN** 系统要求用户确认或验证前置条件