"""使用 Docling 解析 PDF + 按章节分片（本地模型 + TableFormer + OCR）

使用说明：
1. 先手动下载所需模型（layout + tableformer + rapidocr）
2. 运行测试

手动下载模型命令：
  cd /home/buff/workspace/buff/smartcard-agent
  export HF_ENDPOINT=https://hf-mirror.com
  .venv/bin/docling-tools models download --output-dir data/models/docling layout tableformer rapidocr

已启用的功能：
  - layout 版面分析
  - tableformer 表格识别
  - rapidocr OCR（中文+英文）
  - 按章节分片（顺序遍历 + 大小控制 + 重叠）
"""

import json
import pytest
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from pypdf import PdfReader
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.datamodel.settings import settings
from docling_core.types.doc.labels import DocItemLabel


# ===== 本地模型路径 =====
LOCAL_ARTIFACTS_PATH = Path("/home/buff/workspace/buff/smartcard-agent/data/models/docling")

# ===== 分片配置 =====
MAX_CHUNK_CHARS = 4000   # 单个 chunk 最大字符数
OVERLAP_CHARS = 200      # 重叠字符数


@dataclass
class DocumentChunk:
    """文档分片"""
    chunk_id: int
    heading: str           # 所属章节标题（完整路径）
    heading_level: int     # 标题层级
    page_start: int        # 起始页码
    page_end: int          # 结束页码
    text: str              # 文本内容（cleaned）
    char_count: int        # 字符数
    overlap: str           # 与前一块的重叠内容
    is_subchunk: bool      # 是否为二次切分的子块


def split_with_overlap(heading, text, max_chars, overlap) -> list[DocumentChunk]:
    """带重叠的二次切分"""
    sub_chunks = []
    start = 0
    part_num = 0

    while start < len(text):
        end = start + max_chars
        part_num += 1

        if start > 0:
            overlap_start = max(0, start - overlap)
            overlap_text = text[overlap_start:start]
            chunk_text = overlap_text + "\n\n---\n\n" + text[start:end]
        else:
            chunk_text = text[start:end]
            overlap_text = ""

        sub_chunks.append(DocumentChunk(
            chunk_id=0,
            heading=f"{heading} (part {part_num})",
            heading_level=0,
            page_start=0,
            page_end=0,
            text=chunk_text,
            char_count=len(chunk_text),
            overlap=overlap_text,
            is_subchunk=True
        ))

        start = end

    return sub_chunks


def estimate_heading_level(heading_text: str) -> int:
    """从标题文本估算层级（如 "1.1.2" → 3, "A." → 1）"""
    import re

    # 尝试匹配数字层级：1.1.2, 1.2.3.4
    match = re.match(r'^(\d+(?:\.\d+)*)', heading_text)
    if match:
        return len(match.group(1).split('.'))

    # 尝试匹配字母层级：A., B.
    match = re.match(r'^([A-Z])\.', heading_text)
    if match:
        return 1

    # 尝试匹配罗马数字：I., II., III.
    match = re.match(r'^(I{1,3}|IV|VI{0,3}|IX)\.', heading_text)
    if match:
        return 1

    return 1


def chunk_by_reading_order(doc, max_chars=MAX_CHUNK_CHARS, overlap=OVERLAP_CHARS):
    """按阅读顺序分片：顺序遍历，遇到标题时更新当前标题"""

    sections = {}  # key: heading_path -> {"texts": [], "pages": [], "level": int}
    
    # 标题栈：维护当前的标题层级路径
    heading_stack = []  # [(level, heading_text), ...]
    
    for item in doc.texts:
        # 遇到标题 → 更新标题栈
        if item.label == DocItemLabel.SECTION_HEADER:
            # 尝试从标题文本提取层级（如 "1.1.2" → level 3）
            heading_text = item.text
            level = estimate_heading_level(heading_text)
            
            # 弹出比当前 level 更深或相等的标题
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            
            # 压入新标题
            heading_stack.append((level, heading_text))
            continue
        
        # 跳过页眉页脚
        if item.label in [DocItemLabel.PAGE_HEADER, DocItemLabel.PAGE_FOOTER]:
            continue
        
        # 获取当前标题路径
        if heading_stack:
            heading_path = " > ".join([h[1] for h in heading_stack])
            current_level = heading_stack[-1][0]
        else:
            heading_path = "(文档根)"
            current_level = 0
        
        if heading_path not in sections:
            sections[heading_path] = {"texts": [], "pages": [], "level": current_level}
        
        if item.text:
            sections[heading_path]["texts"].append(item.text)
            if item.prov:
                sections[heading_path]["pages"].append(item.prov[0].page_no)

    # 生成 chunks
    chunks = []
    chunk_id = 0

    for heading, data in sections.items():
        full_text = "\n".join(data["texts"])

        if not full_text.strip():
            continue

        page_start = min(data["pages"]) if data["pages"] else 0
        page_end = max(data["pages"]) if data["pages"] else 0

        if len(full_text) <= max_chars:
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                heading=heading,
                heading_level=data["level"],
                page_start=page_start,
                page_end=page_end,
                text=full_text,
                char_count=len(full_text),
                overlap="",
                is_subchunk=False
            ))
            chunk_id += 1
        else:
            sub_chunks = split_with_overlap(
                heading=heading,
                text=full_text,
                max_chars=max_chars,
                overlap=overlap
            )
            for sc in sub_chunks:
                sc.chunk_id = chunk_id
                sc.page_start = page_start
                sc.page_end = page_end
                sc.heading_level = data["level"]
                chunk_id += 1
                chunks.append(sc)

    return chunks


def test_parse_pdf_with_docling_local_model():
    """使用 Docling + 本地模型解析前 50 页 PDF，按章节分片导出"""
    pdf_path = Path(__file__).parent / "GPC_Specification_v2.3_first_50.pdf"
    output_path = Path(__file__).parent / "gpc_first_50_docling_chunks.json"

    if not pdf_path.exists():
        pytest.skip(f"PDF 文件不存在: {pdf_path}")

    if not LOCAL_ARTIFACTS_PATH.exists():
        pytest.skip(f"本地模型目录不存在: {LOCAL_ARTIFACTS_PATH}")

    print(f"\n开始解析: {pdf_path.name}")
    print(f"文件大小: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")

    # 配置 pipeline
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.artifacts_path = LOCAL_ARTIFACTS_PATH
    pipeline_options.ocr_options = RapidOcrOptions()
    settings.artifacts_path = LOCAL_ARTIFACTS_PATH

    pdf_format_option = PdfFormatOption(pipeline_options=pipeline_options)
    format_options = {InputFormat.PDF: pdf_format_option}
    converter = DocumentConverter(format_options=format_options)

    # 解析 PDF
    result = converter.convert(str(pdf_path))
    doc = result.document

    # 按章节分片
    print(f"\n开始按章节分片...")
    print(f"  最大 chunk 字符数: {MAX_CHUNK_CHARS}")
    print(f"  重叠字符数: {OVERLAP_CHARS}")

    chunks = chunk_by_reading_order(doc)

    print(f"\n分片完成！")
    print(f"  总 chunk 数: {len(chunks)}")

    subchunks = sum(1 for c in chunks if c.is_subchunk)
    print(f"  需要二次切分的章节: {subchunks}")

    # 导出为 JSON
    chunks_data = [asdict(c) for c in chunks]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)

    print(f"\n分片结果已导出到: {output_path}")
    print(f"文件大小: {output_path.stat().st_size / 1024:.1f} KB")

    # 打印前 10 个 chunk 预览
    print(f"\n前 10 个 chunk 预览:")
    for c in chunks[:10]:
        print(f"\n  Chunk {c.chunk_id}: [{c.heading}]")
        print(f"    层级: {c.heading_level}")
        print(f"    页码: {c.page_start}-{c.page_end}")
        print(f"    字符数: {c.char_count}")
        print(f"    预览: {c.text[:80]}...")

    assert len(chunks) > 0, "分片结果为空"
    assert output_path.exists(), "输出文件未生成"

