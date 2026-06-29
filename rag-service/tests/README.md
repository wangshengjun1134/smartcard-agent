# PDF 解析测试

## 测试文件

| 测试文件 | 框架 | 说明 |
|---------|------|------|
| `tests/test_pdf_parser.py` | Docling | PDF 文本提取 + 版面分析 |
| `tests/test_unstructured_pdf.py` | Unstructured | PDF 解析 + 表格识别（使用本地模型） |

## Docling 测试

```bash
cd /home/buff/workspace/buff/smartcard-agent/agent-service

# 运行所有 Docling 测试
../.venv/bin/python -m pytest tests/test_pdf_parser.py -v -s

# 运行单个测试（带详细输出）
../.venv/bin/python -m pytest tests/test_pdf_parser.py::test_parse_pdf_with_docling -v -s

# 只运行导入测试（快速验证）
../.venv/bin/python -m pytest tests/test_pdf_parser.py::test_docling_import -v
```

**注意：**
- Docling 默认启用 OCR，首次运行会下载模型
- 测试中已配置 `do_ocr = False` 禁用 OCR
- 版面分析模型仍会加载（约几百 MB）

## Unstructured 测试

```bash
cd /home/buff/workspace/buff/smartcard-agent/agent-service

# 运行所有 Unstructured 测试
../.venv/bin/python -m pytest tests/test_unstructured_pdf.py -v -s

# 运行 fast 策略（快速文本提取，无需模型）
../.venv/bin/python -m pytest tests/test_unstructured_pdf.py::test_parse_pdf_fast_strategy -v -s

# 运行 hi_res 策略（使用本地 YOLOX 模型，含表格识别）
../.venv/bin/python -m pytest tests/test_unstructured_pdf.py::test_parse_gpc_specification_with_local_model -v -s
```

**注意：**
- `fast` 策略：仅提取文本，速度快，无需模型
- `hi_res` 策略：识别表格结构，使用本地模型（已手动下载到 `data/models/yolo_x_layout/`）
- 本地模型路径写死在测试代码中，无需运行时下载

### 本地模型配置

测试代码通过 `register_local_model()` 函数注册本地 YOLOX 模型：

```python
# 本地模型路径（写死在代码中）
LOCAL_MODEL_DIR = "/home/buff/workspace/buff/smartcard-agent/data/models/yolo_x_layout"
LOCAL_MODEL_PATH = f"{LOCAL_MODEL_DIR}/yolox_l0.05.onnx"
LOCAL_LABEL_MAP = f"{LOCAL_MODEL_DIR}/label_map.json"
```

## 直接运行测试脚本

```bash
cd /home/buff/workspace/buff/smartcard-agent

# Unstructured 直接测试脚本
.venv/bin/python agent-service/tests/test_unstructured_parse.py
```
