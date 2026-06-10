---
name: read_iccid
description: 读取 ICCID（集成电路卡识别码）
category: composite
requires_pin: false
dangerous: false
---

# Read ICCID

读取智能卡的 ICCID（Integrated Circuit Card Identifier）。

## APDU 流程

1. `SELECT MF (3F00)` — 选择主文件
2. `SELECT EF_ICCID (2FE2)` — 选择 ICCID 文件
3. `READ BINARY` — 读取 10 字节 ICCID 数据

## 返回数据

- `iccid`: 十六进制字符串
- `iccid_raw`: 原始数据

## 注意事项

- 需要已连接读卡器
- 适用于 ISO7816 标准卡片
