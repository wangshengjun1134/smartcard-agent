#!/usr/bin/env python3
"""Download BGE-m3 model to local directory."""

import os
from pathlib import Path

from sentence_transformers import SentenceTransformer


def download_bge_m3(
    save_dir: str = "data/models/bge-m3",
    model_name: str = "BAAI/bge-m3",
):
    """Download and save BGE-m3 model.

    Args:
        save_dir: Directory to save the model.
        model_name: HuggingFace model name.
    """
    save_path = Path(save_dir)

    # 如果已存在，跳过下载
    if save_path.exists():
        print(f"Model already exists at: {save_path}")
        return

    # 创建目录
    save_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {model_name} from HuggingFace...")
    print("This may take a few minutes (~2GB)...")

    # 下载模型
    model = SentenceTransformer(model_name)

    # 保存到本地
    model.save(str(save_path))

    print(f"✓ Model saved to: {save_path}")
    print(f"  Size: {sum(f.stat().st_size for f in save_path.rglob('*') if f.is_file()) / 1024**3:.2f} GB")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download BGE-m3 model")
    parser.add_argument(
        "--save-dir",
        type=str,
        default="data/models/bge-m3",
        help="Directory to save the model",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="BAAI/bge-m3",
        help="HuggingFace model name",
    )

    args = parser.parse_args()

    download_bge_m3(save_dir=args.save_dir, model_name=args.model_name)