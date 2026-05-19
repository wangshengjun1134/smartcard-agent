#!/usr/bin/env python3
"""
Build script for packaging Python service as Tauri Sidecar executable.

This script uses PyInstaller to create a standalone executable that can be
bundled with the Tauri application.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def build_sidecar():
    """Build the Python service as a sidecar executable."""
    project_root = get_project_root()
    python_service = project_root / "python-service"
    src_dir = python_service / "src"
    bin_dir = python_service / "bin"

    # Ensure bin directory exists
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Determine output filename based on platform
    if sys.platform == "win32":
        exe_name = "python-service.exe"
    elif sys.platform == "darwin":
        exe_name = "python-service"
    else:
        exe_name = "python-service"

    output_path = bin_dir / exe_name

    # PyInstaller arguments
    pyinstaller_args = [
        "pyinstaller",
        "--onefile",  # Single executable file
        "--name", "python-service",
        "--distpath", str(bin_dir),
        "--workpath", str(python_service / "build" / "pyinstaller_work"),
        "--specpath", str(python_service / "build"),
        "--clean",
        str(src_dir / "main.py"),
    ]

    # Add hidden imports for FastAPI and dependencies
    hidden_imports = [
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "starlette",
        "starlette.responses",
        "starlette.routing",
        "starlette.middleware",
        "starlette.middleware.cors",
        "aiofiles",
        "aiofiles.os",
        "pydantic",
    ]

    for module in hidden_imports:
        pyinstaller_args.extend(["--hidden-import", module])

    # Add data files (if any)
    # pyinstaller_args.extend(["--add-data", f"{src_dir}:{src_dir.name}"])

    print(f"Building sidecar executable: {output_path}")
    print(f"Running: {' '.join(pyinstaller_args)}")

    # Run PyInstaller
    result = subprocess.run(pyinstaller_args, cwd=str(python_service))

    if result.returncode != 0:
        print(f"Error: PyInstaller failed with code {result.returncode}")
        sys.exit(1)

    # Verify output
    if output_path.exists():
        print(f"Success: Built {output_path}")
        print(f"Size: {output_path.stat().st_size / (1024*1024):.2f} MB")
    else:
        print(f"Error: Output file not found at {output_path}")
        sys.exit(1)

    # Clean up spec file
    spec_file = python_service / "build" / "python-service.spec"
    if spec_file.exists():
        spec_file.unlink()


if __name__ == "__main__":
    build_sidecar()