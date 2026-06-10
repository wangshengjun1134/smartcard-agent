"""Skill Metadata definitions.

This module provides metadata structures and validation for skills.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class SkillCategory(Enum):
    """Skill category enumeration."""

    PRIMITIVE = "primitive"
    COMPOSITE = "composite"
    EXPLORATORY = "exploratory"
    WORKFLOW = "workflow"


class SkillSecurityLevel(Enum):
    """Skill security level."""

    SAFE = "safe"  # No security requirements
    PIN_REQUIRED = "pin_required"  # Requires PIN verification
    SECURE_CHANNEL = "secure_channel"  # Requires secure channel
    DANGEROUS = "dangerous"  # Can cause permanent changes


@dataclass
class SkillMetadata:
    """Complete skill metadata structure.

    Attributes:
        name: Unique skill name
        description: Human-readable description
        category: Skill category
        security_level: Security requirements
        supported_card_types: Card types this skill supports
        required_capabilities: Required card capabilities
        params_schema: Parameter validation schema
        result_schema: Expected result structure
        retry_policy: Retry behavior configuration
        timeout: Maximum execution time in seconds
    """

    name: str
    description: str
    category: SkillCategory = SkillCategory.PRIMITIVE
    security_level: SkillSecurityLevel = SkillSecurityLevel.SAFE
    supported_card_types: List[str] = None
    required_capabilities: List[str] = None
    params_schema: Dict[str, Any] = None
    result_schema: Dict[str, Any] = None
    retry_policy: Dict[str, Any] = None
    timeout: float = 30.0

    def __post_init__(self):
        """Set defaults."""
        if self.supported_card_types is None:
            self.supported_card_types = []
        if self.required_capabilities is None:
            self.required_capabilities = []
        if self.params_schema is None:
            self.params_schema = {}
        if self.result_schema is None:
            self.result_schema = {}
        if self.retry_policy is None:
            self.retry_policy = {
                "max_retries": 3,
                "retry_delay": 0.5,
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "security_level": self.security_level.value,
            "supported_card_types": self.supported_card_types,
            "required_capabilities": self.required_capabilities,
            "params_schema": self.params_schema,
            "result_schema": self.result_schema,
            "retry_policy": self.retry_policy,
            "timeout": self.timeout,
        }


# Common parameter schemas
FID_PARAM_SCHEMA = {
    "fid": {
        "type": "string",
        "pattern": "^[0-9A-Fa-f]{4}$",
        "description": "File ID (4 hex characters)",
        "required": True,
    }
}

AID_PARAM_SCHEMA = {
    "aid": {
        "type": "string",
        "pattern": "^[0-9A-Fa-f]+$",
        "description": "Application ID (hex string)",
        "required": True,
    }
}

READ_BINARY_PARAM_SCHEMA = {
    "offset": {
        "type": "integer",
        "min": 0,
        "max": 65535,
        "description": "Byte offset to read from",
        "default": 0,
    },
    "length": {
        "type": "integer",
        "min": 0,
        "max": 256,
        "description": "Number of bytes to read (0 = all available)",
        "default": 0,
    }
}

READ_RECORD_PARAM_SCHEMA = {
    "record_number": {
        "type": "integer",
        "min": 1,
        "description": "Record number to read",
        "default": 1,
    },
    "length": {
        "type": "integer",
        "min": 0,
        "description": "Number of bytes to read",
        "default": 0,
    }
}

PIN_PARAM_SCHEMA = {
    "pin": {
        "type": "string",
        "pattern": "^[0-9]{4,8}$",
        "description": "PIN value (4-8 digits)",
        "required": True,
    },
    "pin_ref": {
        "type": "integer",
        "min": 1,
        "max": 10,
        "description": "PIN reference number",
        "default": 1,
    }
}


def validate_params(schema: Dict[str, Any], params: Dict[str, Any]) -> tuple[bool, str]:
    """Validate parameters against schema.

    Args:
        schema: Parameter schema
        params: Parameters to validate

    Returns:
        Tuple of (valid, error_message).
    """
    for param_name, param_def in schema.items():
        if param_def.get("required", False):
            if param_name not in params:
                return False, f"Missing required parameter: {param_name}"

        if param_name in params:
            value = params[param_name]

            # Type check
            expected_type = param_def.get("type")
            if expected_type == "integer":
                if not isinstance(value, int):
                    return False, f"Parameter {param_name} must be integer"
                if "min" in param_def and value < param_def["min"]:
                    return False, f"Parameter {param_name} must be >= {param_def['min']}"
                if "max" in param_def and value > param_def["max"]:
                    return False, f"Parameter {param_name} must be <= {param_def['max']}"

            elif expected_type == "string":
                if not isinstance(value, str):
                    return False, f"Parameter {param_name} must be string"
                if "pattern" in param_def:
                    import re
                    if not re.match(param_def["pattern"], value):
                        return False, f"Parameter {param_name} doesn't match pattern {param_def['pattern']}"

    return True, ""


def create_metadata(
    name: str,
    description: str,
    category: SkillCategory = SkillCategory.PRIMITIVE,
    **kwargs,
) -> SkillMetadata:
    """Create skill metadata with defaults.

    Args:
        name: Skill name
        description: Description
        category: Category
        **kwargs: Additional metadata fields

    Returns:
        SkillMetadata instance.
    """
    return SkillMetadata(
        name=name,
        description=description,
        category=category,
        **kwargs,
    )