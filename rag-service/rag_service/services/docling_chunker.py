"""Docling-based PDF chunking service.

Uses Docling for PDF parsing and chunks documents by heading hierarchy
with size control and overlap for oversized sections.
"""

import re
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.datamodel.settings import settings
from docling_core.types.doc.labels import DocItemLabel


logger = logging.getLogger(__name__)


# ===== 分片配置 =====
MAX_CHUNK_CHARS = 4000   # 单个 chunk 最大字符数
OVERLAP_CHARS = 200      # 重叠字符数
DEFAULT_ARTIFACTS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "models" / "docling"


@dataclass
class DocumentChunk:
    """文档分片（中间数据）"""
    chunk_id: int
    heading: str           # 所属章节标题（完整路径）
    heading_level: int     # 标题层级
    page_start: int        # 起始页码
    page_end: int          # 结束页码
    text: str              # 文本内容（cleaned）
    char_count: int        # 字符数
    overlap: str           # 与前一块的重叠内容
    is_subchunk: bool      # 是否为二次切分的子块


def estimate_heading_level(heading_text: str) -> int:
    """从标题文本估算层级（如 "1.1.2" → 3, "A." → 1）"""
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


def chunk_by_reading_order(doc, max_chars=MAX_CHUNK_CHARS, overlap=OVERLAP_CHARS):
    """按阅读顺序分片：顺序遍历，遇到标题时更新当前标题"""

    sections = {}  # key: heading_path -> {"texts": [], "pages": [], "level": int}

    # 标题栈：维护当前的标题层级路径
    heading_stack = []  # [(level, heading_text), ...]

    for item in doc.texts:
        # 遇到标题 → 更新标题栈
        if item.label == DocItemLabel.SECTION_HEADER:
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


def parse_and_chunk_pdf(
    pdf_path: Path,
    *,
    max_chars: int = MAX_CHUNK_CHARS,
    overlap: int = OVERLAP_CHARS,
    artifacts_path: Optional[Path] = None,
    enable_ocr: bool = False,
    enable_tables: bool = False,
) -> list[DocumentChunk]:
    """解析 PDF 并分片
    
    Args:
        pdf_path: PDF 文件路径
        max_chars: 单个 chunk 最大字符数
        overlap: 重叠字符数
        artifacts_path: 本地模型路径
        enable_ocr: 是否启用 OCR
        enable_tables: 是否启用表格识别
    
    Returns:
        分片列表
    """
    if artifacts_path is None:
        artifacts_path = DEFAULT_ARTIFACTS_PATH
    
    if not artifacts_path.exists():
        raise FileNotFoundError(
            f"本地模型目录不存在: {artifacts_path}\n"
            f"请先下载模型: docling-tools models download --output-dir {artifacts_path} layout"
        )

    logger.info(f"开始解析 PDF: {pdf_path.name}")
    logger.info(f"模型路径: {artifacts_path}")
    logger.info(f"OCR: {enable_ocr}, 表格识别: {enable_tables}")

    # 配置 pipeline
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = enable_ocr
    pipeline_options.do_table_structure = enable_tables
    pipeline_options.artifacts_path = artifacts_path

    if enable_ocr:
        pipeline_options.ocr_options = RapidOcrOptions()

    settings.artifacts_path = artifacts_path

    # 创建转换器
    pdf_format_option = PdfFormatOption(pipeline_options=pipeline_options)
    format_options = {InputFormat.PDF: pdf_format_option}
    converter = DocumentConverter(format_options=format_options)

    # 解析 PDF
    result = converter.convert(str(pdf_path))
    doc = result.document

    logger.info(f"PDF 解析完成，开始分片...")

    # 分片
    chunks = chunk_by_reading_order(doc, max_chars=max_chars, overlap=overlap)

    logger.info(f"分片完成: {len(chunks)} 个 chunk")

    return chunks
