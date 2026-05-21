## ADDED Requirements

### Requirement: PCSC Client 结构

系统 SHALL 创建 PCSC Client 类，实现 connect, disconnect, send_apdu, reset_card 方法。

#### Scenario: 验证 Client 类
- **WHEN** 检查 `tools/pcsc/client.py`
- **THEN** PcscClient 类包含所有连接和 APDU 方法

### Requirement: 读卡器连接

系统 SHALL 实现 connect() 方法，通过 pyscard 连接第一个可用读卡器。

#### Scenario: 成功连接读卡器
- **WHEN** 存在读卡器且卡片已插入
- **THEN** connect() 成功建立 connection，返回 ATR

#### Scenario: 读卡器不存在
- **WHEN** 没有可用读卡器
- **THEN** connect() 抛出 ReaderNotFoundError

### Requirement: APDU 发送

系统 SHALL 实现 send_apdu(apdu) 方法，发送 APDU 命令并返回 {data, sw} 响应。

#### Scenario: 发送 SELECT APDU
- **WHEN** send_apdu([0x00, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00])
- **THEN** 返回 {data: [...], sw: "9000"}

### Requirement: 卡片重置

系统 SHALL 实现 reset_card() 方法，执行卡片冷重置或热重置。

#### Scenario: 执行卡片重置
- **WHEN** 调用 reset_card()
- **THEN** 卡片状态清除，返回新 ATR

### Requirement: 连接异常处理

系统 SHALL 定义 PCSC 异常类：ReaderNotFoundError, CardNotFoundError, APDUError, ConnectionLostError。

#### Scenario: 验证异常定义
- **WHEN** 检查 `tools/pcsc/exceptions.py`
- **THEN** 定义所有 PCSC 相关异常类