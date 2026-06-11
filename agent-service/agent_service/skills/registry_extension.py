"""Skill Registry Extension for dynamic plugin discovery.

This module provides automatic discovery and registration of skills
from plugin directories:
- `.skills/` - built-in skills directory
- `external_skills/` - user-custom skills directory
- `SKILL_DIRS` env var - additional custom directories

Each skill plugin is a directory containing:
- `skill.md` (preferred) or `skill.json` - metadata
- `__init__.py` - skill implementation with register() function

Example skill.md:
    ---
    name: read_iccid
    description: Read ICCID from smart card
    category: composite
    requires_pin: false
    dangerous: false
    ---

    # Read ICCID

    Read the ICCID from a smart card using ISO 7816 SELECT + READ BINARY.

    ## APDU Flow
    1. SELECT MF (3F00)
    2. SELECT EF_ICCID (2FE2)
    3. READ BINARY (10 bytes)

Example __init__.py:
    from agent_service.skills.base.base_skill import BaseSkill, SkillResult

    class ReadIccidSkill(BaseSkill):
        name = "read_iccid"
        description = "Read ICCID"
        async def run(self, ctx, params): ...

    def register():
        return ReadIccidSkill()
"""

import importlib.util
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Optional

from agent_service.skills.base.registry import get_registry

logger = logging.getLogger(__name__)


def discover_and_register_skills(
    extra_dirs: list[str] | None = None,
) -> Dict[str, str]:
    """Discover and register skills from plugin directories.

    Scans directories in order:
    1. `.skills/` (project root)
    2. `external_skills/` (project root)
    3. Extra dirs from `SKILL_DIRS` env var
    4. Extra dirs from `extra_dirs` parameter

    Args:
        extra_dirs: Additional plugin directories to scan.

    Returns:
        Mapping of skill name -> source directory.
    """
    results = {}
    project_root = Path(__file__).parent.parent.parent

    # Directories to scan, in priority order
    scan_dirs: list[tuple[Path, str]] = [
        (project_root / ".skills", "builtin"),
        (project_root / "external_skills", "external"),
    ]

    # Add env var directories
    env_dirs = os.getenv("SKILL_DIRS", "").split(":")
    for d in env_dirs:
        d = d.strip()
        if d:
            scan_dirs.append((Path(d), "env"))

    # Add parameter directories
    if extra_dirs:
        for d in extra_dirs:
            scan_dirs.append((Path(d), "param"))

    for dir_path, source in scan_dirs:
        if dir_path.exists() and dir_path.is_dir():
            results.update(_scan_directory(dir_path, source))

    logger.info(f"Discovered {len(results)} skills: {list(results.keys())}")
    return results


def _scan_directory(plugin_dir: Path, source: str) -> Dict[str, str]:
    """Scan a directory for skill plugins.

    Args:
        plugin_dir: Directory to scan.
        source: Source label for logging.

    Returns:
        Mapping of skill name -> full path.
    """
    results = {}

    for item in sorted(plugin_dir.iterdir()):
        if not item.is_dir():
            continue

        init_file = item / "__init__.py"
        if not init_file.exists():
            logger.debug(f"Skipping {item.name}: missing __init__.py")
            continue

        # Prefer skill.md, fallback to skill.json
        skill_md = item / "skill.md"
        skill_json = item / "skill.json"

        metadata_file = skill_md if skill_md.exists() else (skill_json if skill_json.exists() else None)
        if metadata_file is None:
            logger.debug(f"Skipping {item.name}: missing skill.md or skill.json")
            continue

        try:
            _load_plugin(item, metadata_file, init_file, source)
            results[item.name] = str(item)
        except Exception as e:
            logger.error(f"Failed to load plugin {item.name}: {e}")

    return results


def _parse_md_frontmatter(content: str) -> Optional[Dict]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown file content.

    Returns:
        Parsed frontmatter dict, or None if no frontmatter found.
    """
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not match:
        return None

    yaml_text = match.group(1)
    metadata = {}

    for line in yaml_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            # Parse basic types
            if value.lower() == 'true':
                metadata[key] = True
            elif value.lower() == 'false':
                metadata[key] = False
            elif value.isdigit():
                metadata[key] = int(value)
            else:
                metadata[key] = value.strip('"').strip("'")

    return metadata


def _load_metadata(file_path: Path) -> Dict:
    """Load metadata from skill.md or skill.json.

    Args:
        file_path: Path to metadata file.

    Returns:
        Metadata dictionary.
    """
    if file_path.suffix == '.md':
        with open(file_path) as f:
            content = f.read()
        metadata = _parse_md_frontmatter(content)
        if metadata is None:
            raise ValueError(f"No YAML frontmatter found in {file_path}")
        return metadata
    else:
        with open(file_path) as f:
            return json.load(f)


def _load_plugin(
    plugin_dir: Path,
    metadata_file: Path,
    init_file: Path,
    source: str,
) -> None:
    """Load and register a single skill plugin.

    Args:
        plugin_dir: Plugin directory.
        metadata_file: Path to skill.md or skill.json.
        init_file: Path to __init__.py.
        source: Source label.
    """
    # Load metadata
    metadata = _load_metadata(metadata_file)

    skill_name = metadata.get("name", plugin_dir.name)
    category = metadata.get("category", "primitive")

    # Dynamically import the plugin module
    module_name = f"_skill_plugin_{plugin_dir.name}"
    spec = importlib.util.spec_from_file_location(module_name, str(init_file))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {init_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Call register() to get skill instance
    if not hasattr(module, "register"):
        raise ImportError(f"Plugin {plugin_dir.name} has no register() function")

    skill = module.register()

    # Register in global registry
    registry = get_registry()
    registry.register(skill, category)
    logger.info(f"Registered skill: {skill_name} ({source}: {plugin_dir.name})")
