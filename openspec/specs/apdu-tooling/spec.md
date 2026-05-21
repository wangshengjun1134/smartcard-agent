## ADDED Requirements

### Requirement: APDU Builder 结构

系统 SHALL 创建 APDU Builder 目录，包含 select_builder, read_builder, auth_builder, secure_channel_builder。

#### Scenario: 验证 Builder 目录
- **WHEN** 检查 `apdu/builders/`
- **THEN** 包含所有 Builder 模块

### Requirement: SELECT APDU Builder

系统 SHALL 实现 build_select_file(fid) 函数，生成符合 ISO 7816 的 SELECT 命令 APDU。

#### Scenario: 构建 SELECT APDU
- **WHEN** 调用 build_select_file("3F00")
- **THEN** 返回 bytes: 00A40000023F00

### Requirement: READ BINARY APDU Builder

系统 SHALL 实现 build_read_binary(offset, length) 函数，生成 READ BINARY 命令 APDU。

#### Scenario: 构建 READ BINARY APDU
- **WHEN** 调用 build_read_binary(0, 9)
- **THEN** 返回 bytes: 00B0000009

### Requirement: TLV Parser

系统 SHALL 实现 parse_tlv(data) 函数，解析 BER-TLV 结构数据。

#### Scenario: 解析 TLV 数据
- **WHEN** 输入 TLV 编码数据
- **THEN** 返回解析后的 Tag-Length-Value 结构字典

### Requirement: FCP Parser

系统 SHALL 实现 parse_fcp(data) 函数，解析 File Control Parameters。

#### Scenario: 解析 FCP
- **WHEN** SELECT 响应包含 FCP TLV
- **THEN** 返回文件大小、类型、访问条件等属性

### Requirement: SW Parser

系统 SHALL 实现 decode_sw(sw) 函数，解析 Status Word 含义。

#### Scenario: 解析成功 SW
- **WHEN** decode_sw("9000")
- **THEN** 返回含义: "正常完成"

#### Scenario: 解析错误 SW
- **WHEN** decode_sw("6982")
- **THEN** 返回含义: "安全条件不满足"

### Requirement: APDU Constants

系统 SHALL 创建 constants 目录，定义 sw_codes, file_ids, instructions 常量映射。

#### Scenario: 验证常量定义
- **WHEN** 检查 `apdu/constants/sw_codes.py`
- **THEN** 包含常见 SW 码映射表