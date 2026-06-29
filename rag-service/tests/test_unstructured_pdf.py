"""使用 Unstructured hi_res 策略解析 PDF（本地模型）"""

import pytest
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from unstructured.partition.pdf import partition_pdf


# ===== 本地模型路径 =====
LOCAL_MODEL_DIR = "/home/buff/workspace/buff/smartcard-agent/data/models/yolo_x_layout"
LOCAL_MODEL_PATH = f"{LOCAL_MODEL_DIR}/yolox_l0.05.onnx"
LOCAL_LABEL_MAP = f"{LOCAL_MODEL_DIR}/label_map.json"
LOCAL_MODEL_NAME = "local_yolox"
TABLE_MODEL_PATH = "/home/buff/workspace/buff/models/table-transformer-structure-recognition"


def register_local_models():
    """注册本地模型到 unstructured_inference"""
    import json
    from unstructured_inference.models.base import register_new_model
    from unstructured_inference.models.yolox import UnstructuredYoloXModel
    from unstructured_inference.models import tables

    with open(LOCAL_LABEL_MAP, 'r') as f:
        label_map = json.load(f)

    register_new_model(
        model_config={LOCAL_MODEL_NAME: {"model_path": LOCAL_MODEL_PATH, "label_map": label_map}},
        model_class=UnstructuredYoloXModel,
    )
    print(f"已注册本地布局模型: {LOCAL_MODEL_NAME}")

    print(f"初始化本地表格模型: {TABLE_MODEL_PATH}")
    tables.tables_agent.initialize(model=TABLE_MODEL_PATH)
    print(f"本地表格模型初始化完成")


def test_parse_pdf_hi_res_export_to_file():
    """使用 hi_res 策略解析前 50 页 PDF，结果导出到可读文件"""
    pdf_path = Path(__file__).parent / "GPC_Specification_v2.3.pdf"
    temp_pdf = Path(__file__).parent / "GPC_Specification_v2.3_first_50.pdf"
    output_path = Path(__file__).parent / "gpc_first_50_parsed_output.txt"

    if not pdf_path.exists():
        pytest.skip(f"PDF 文件不存在: {pdf_path}")

    # 生成前 50 页测试文档
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    num_pages = min(50, len(reader.pages))
    for i in range(num_pages):
        writer.add_page(reader.pages[i])
    with open(temp_pdf, 'wb') as f:
        writer.write(f)

    print(f"\n开始解析: {temp_pdf.name} ({num_pages} 页)")
    print(f"使用本地 YOLOX 模型: {LOCAL_MODEL_PATH}")
    print(f"使用本地 Table 模型: {TABLE_MODEL_PATH}")

    register_local_models()

    elements = partition_pdf(
        filename=str(temp_pdf),
        strategy="hi_res",
        infer_table_structure=True,
        hi_res_model_name=LOCAL_MODEL_NAME,
    )

    # 统计元素类型
    element_types = {}
    for el in elements:
        element_types[el.category] = element_types.get(el.category, 0) + 1

    print(f"\n解析完成！共提取 {len(elements)} 个元素")
    print("\n元素类型分布:")
    for category, count in sorted(element_types.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}")

    # 导出到文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"=== GPC Specification v2.3 前 50 页解析结果 ===\n")
        f.write(f"源文件: {pdf_path.name}\n")
        f.write(f"元素总数: {len(elements)}\n")
        f.write(f"=" * 60 + "\n\n")

        f.write("【元素类型分布】\n")
        for category, count in sorted(element_types.items(), key=lambda x: -x[1]):
            f.write(f"  {category}: {count}\n")
        f.write("\n" + "=" * 60 + "\n\n")

        for i, el in enumerate(elements, 1):
            f.write(f"\n--- 元素 {i} [{el.category}] ---\n")
            f.write(f"{el.text}\n")
            if el.category == "Table" and hasattr(el.metadata, 'text_as_html'):
                f.write(f"\n[HTML 格式]\n{el.metadata.text_as_html}\n")

    print(f"\n解析结果已导出到: {output_path}")
    print(f"文件大小: {output_path.stat().st_size / 1024:.1f} KB")

    assert len(elements) > 0, "未提取到任何元素"
    assert output_path.exists(), "输出文件未生成"
