"""Skill Registry Extension - Auto-registration and organization.

This module provides utilities for registering all skill categories
and organizing the skill hierarchy.
"""

from typing import Dict, Any, List
from skills.base.registry import SkillRegistry, get_registry


# Skill category definitions
SKILL_CATEGORIES = {
    # A. Reader / Session Primitive
    "reader": {
        "skills": [
            "connect", "disconnect", "reconnect", "reset_card",
            "get_reader_info", "on_card", "session_management",
        ],
        "description": "Card reader and session management",
        "count": 7,
    },

    # B. ISO7816 Core Primitive
    "iso7816": {
        "skills": [
            "send_apdu", "select", "read_binary", "read_record",
            "get_response", "verify", "change_pin", "unblock_pin",
            "get_challenge", "internal_authenticate", "manage_channel",
        ],
        "description": "ISO7816-4 core commands",
        "count": 11,
    },

    # C. FileSystem Primitive
    "filesystem": {
        "skills": [
            "select_mf", "select_df", "select_ef", "resolve_path",
            "read_transparent_ef", "read_linear_fixed_ef",
            "discover_applications",
        ],
        "description": "File system navigation and operations",
        "count": 7,
    },

    # D. Security Primitive
    "security": {
        "skills": [
            "verify_pin", "verify_adm", "get_pin_status",
            "change_pin", "unblock_pin",
            "open_secure_channel", "close_secure_channel",
            "wrap_secure_apdu", "calculate_mac",
        ],
        "description": "Authentication and secure channel",
        "count": 9,
    },

    # E. SCP80 Primitive
    "scp80": {
        "skills": [
            "establish_scp80", "send_secured_sms",
            "build_ota_packet", "encrypt_ota_packet",
            "calculate_ota_mac",
        ],
        "description": "SCP80 OTA operations",
        "count": 5,
    },

    # F. SCP03 Primitive
    "scp03": {
        "skills": [
            "scp03_initialize_update", "scp03_external_authenticate",
            "scp03_wrap", "scp03_unwrap",
            "scp03_encrypt", "scp03_mac", "scp03_rmac",
        ],
        "description": "SCP03 secure channel",
        "count": 7,
    },

    # G. GlobalPlatform Primitive
    "globalplatform": {
        "skills": [
            "gp_select_isd", "gp_get_status", "gp_install",
            "gp_load", "gp_delete", "gp_put_key",
            "gp_store_data", "gp_set_status",
        ],
        "description": "GlobalPlatform card management",
        "count": 8,
    },

    # H. JavaCard Primitive
    "javacard": {
        "skills": [
            "jc_install_applet", "jc_delete_applet",
            "jc_select_applet", "jc_send_apdu",
            "jc_get_applet_info",
        ],
        "description": "JavaCard applet operations",
        "count": 5,
    },

    # I. eUICC Primitive
    "euicc": {
        "skills": [
            "euicc_get_eid", "euicc_list_profiles",
            "euicc_enable_profile", "euicc_disable_profile",
            "euicc_delete_profile", "euicc_download_profile",
            "euicc_get_profile_info", "euicc_set_nickname",
            "euicc_reset_memory", "euicc_get_config",
        ],
        "description": "eUICC profile management",
        "count": 10,
    },

    # J. Discovery Primitive
    "discovery": {
        "skills": [
            "detect_card_type", "detect_usim", "detect_isim",
            "detect_euicc", "detect_scp", "detect_gp",
            "probe_capabilities", "fingerprint_card",
        ],
        "description": "Card capability detection",
        "count": 8,
    },

    # K. Runtime Primitive
    "runtime": {
        "skills": [
            "save_checkpoint", "restore_checkpoint",
            "rollback", "replay", "retry_last_action",
            "validate_runtime_state", "verify_preconditions",
            "resolve_next_action", "audit_log",
        ],
        "description": "Runtime state management",
        "count": 9,
    },
}


def register_all_skills(registry: SkillRegistry = None) -> Dict[str, int]:
    """Register all skills from all categories.

    Args:
        registry: Registry to register skills (default: global registry)

    Returns:
        Dictionary of category -> skill count.
    """
    if registry is None:
        registry = get_registry()

    counts = {}

    # Register Reader skills
    try:
        from skills.primitive.connect import register_reader_skills
        register_reader_skills(registry)
        counts["reader"] = SKILL_CATEGORIES["reader"]["count"]
    except Exception:
        counts["reader"] = 0

    # Register ISO7816 skills
    try:
        from skills.primitive.iso7816 import register_iso7816_skills
        register_iso7816_skills(registry)
        counts["iso7816"] = SKILL_CATEGORIES["iso7816"]["count"]
    except Exception:
        counts["iso7816"] = 0

    # Register FileSystem skills
    try:
        from skills.filesystem import register_filesystem_skills
        register_filesystem_skills(registry)
        counts["filesystem"] = SKILL_CATEGORIES["filesystem"]["count"]
    except Exception:
        counts["filesystem"] = 0

    # Register Security skills
    try:
        from skills.security import register_security_skills
        register_security_skills(registry)
        counts["security"] = SKILL_CATEGORIES["security"]["count"]
    except Exception:
        counts["security"] = 0

    # Register SCP80 skills
    try:
        from skills.scp80 import register_scp80_skills
        register_scp80_skills(registry)
        counts["scp80"] = SKILL_CATEGORIES["scp80"]["count"]
    except Exception:
        counts["scp80"] = 0

    # Register SCP03 skills
    try:
        from skills.scp03 import register_scp03_skills
        register_scp03_skills(registry)
        counts["scp03"] = SKILL_CATEGORIES["scp03"]["count"]
    except Exception:
        counts["scp03"] = 0

    # Register GlobalPlatform skills
    try:
        from skills.globalplatform import register_globalplatform_skills
        register_globalplatform_skills(registry)
        counts["globalplatform"] = SKILL_CATEGORIES["globalplatform"]["count"]
    except Exception:
        counts["globalplatform"] = 0

    # Register JavaCard skills
    try:
        from skills.javacard import register_javacard_skills
        register_javacard_skills(registry)
        counts["javacard"] = SKILL_CATEGORIES["javacard"]["count"]
    except Exception:
        counts["javacard"] = 0

    # Register eUICC skills
    try:
        from skills.euicc import register_euicc_skills
        register_euicc_skills(registry)
        counts["euicc"] = SKILL_CATEGORIES["euicc"]["count"]
    except Exception:
        counts["euicc"] = 0

    # Register Discovery skills
    try:
        from skills.discovery import register_discovery_skills
        register_discovery_skills(registry)
        counts["discovery"] = SKILL_CATEGORIES["discovery"]["count"]
    except Exception:
        counts["discovery"] = 0

    # Register Runtime skills
    try:
        from skills.runtime_primitive import register_runtime_skills
        register_runtime_skills(registry)
        counts["runtime"] = SKILL_CATEGORIES["runtime"]["count"]
    except Exception:
        counts["runtime"] = 0

    return counts


def get_skill_categories() -> Dict[str, Dict[str, Any]]:
    """Get skill category definitions.

    Returns:
        Dictionary of category -> definition.
    """
    return SKILL_CATEGORIES


def get_skills_by_category(category: str) -> List[str]:
    """Get skill names by category.

    Args:
        category: Category name

    Returns:
        List of skill names.
    """
    return SKILL_CATEGORIES.get(category, {}).get("skills", [])


def get_total_skill_count() -> int:
    """Get total number of defined skills.

    Returns:
        Total skill count.
    """
    total = 0
    for category in SKILL_CATEGORIES:
        total += SKILL_CATEGORIES[category].get("count", len(SKILL_CATEGORIES[category]["skills"]))
    return total


def print_skill_summary() -> None:
    """Print skill summary."""
    print("Skill Categories Summary:")
    print("=" * 60)

    for category, info in SKILL_CATEGORIES.items():
        skill_count = info.get("count", len(info["skills"]))
        print(f"{category:15} : {skill_count:3} skills - {info['description']}")

    print("=" * 60)
    print(f"Total: {get_total_skill_count()} skills defined")


# Auto-registration on import (optional)
# Uncomment to auto-register on module import:
# register_all_skills()