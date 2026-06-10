"""Base Skill class for smart card operations.

This module defines the BaseSkill base class that all skills inherit from.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SkillResult:
    """Result of a skill execution."""

    success: bool
    data: Optional[bytes] = None
    sw: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseSkill(ABC):
    """Base class for all skills.

    Skills are operations that can be executed on a smart card.
    Each skill has metadata describing its properties and a run method
    for execution.

    Attributes:
        name: Unique skill name
        description: Human-readable description
        dangerous: Whether the skill can cause permanent changes
        requires_pin: Whether PIN verification is required
        requires_secure_channel: Whether secure channel is required
        supported_card_types: List of card types this skill supports
        required_capabilities: Capabilities required for this skill

    Example:
        class SelectFileSkill(BaseSkill):
            name = "select_file"
            description = "Select a file by FID"

            async def run(self, ctx, params):
                fid = params["fid"]
                apdu = build_select_file(fid)
                response = await ctx.pcsc.send_apdu(apdu)
                return SkillResult(success=True, sw=response.sw)
    """

    name: str = "base"
    description: str = ""
    dangerous: bool = False
    requires_pin: bool = False
    pin_reference: int = 1  # Default PIN reference
    requires_secure_channel: bool = False
    secure_channel_protocol: Optional[str] = None
    supported_card_types: list = []  # Empty means all cards
    required_capabilities: list = []

    @abstractmethod
    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute the skill.

        Args:
            ctx: Runtime context with PCSC client and state
            params: Skill parameters

        Returns:
            SkillResult with execution outcome.
        """
        raise NotImplementedError

    def can_execute(self, ctx: Any) -> tuple[bool, str]:
        """Check if skill can be executed with current context.

        Args:
            ctx: Runtime context

        Returns:
            Tuple of (can_execute, reason_if_not)
        """
        # Check connection
        if not ctx.runtime_ctx.connected:
            return False, "Not connected to card"

        return True, ""

    def get_metadata(self) -> Dict[str, Any]:
        """Get skill metadata.

        Returns:
            Dictionary of skill metadata.
        """
        return {
            "name": self.name,
            "description": self.description,
            "dangerous": self.dangerous,
            "requires_pin": self.requires_pin,
            "pin_reference": self.pin_reference,
            "requires_secure_channel": self.requires_secure_channel,
            "secure_channel_protocol": self.secure_channel_protocol,
            "supported_card_types": self.supported_card_types,
            "required_capabilities": self.required_capabilities,
        }

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """Validate skill parameters.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (valid, error_if_not)
        """
        # Default implementation - subclasses should override
        return True, ""


class SkillExecutionContext:
    """Context for skill execution.

    Provides access to:
    - PCSC client for APDU operations
    - Runtime context for state management
    - Skill registry for nested skill calls
    """

    def __init__(
        self,
        pcsc_client: Any,
        runtime_context: Any,
        skill_registry: Any = None,
    ):
        """Initialize skill execution context.

        Args:
            pcsc_client: PCSC client instance
            runtime_context: Runtime context instance
            skill_registry: Skill registry for nested calls
        """
        self.pcsc = pcsc_client
        self.runtime_ctx = runtime_context
        self.skill_registry = skill_registry

    async def execute_skill(
        self,
        skill_name: str,
        params: Dict[str, Any],
    ) -> SkillResult:
        """Execute another skill from this context.

        Args:
            skill_name: Name of skill to execute
            params: Skill parameters

        Returns:
            SkillResult from the executed skill.
        """
        if self.skill_registry is None:
            return SkillResult(success=False, error="Skill registry not available")

        skill = self.skill_registry.get_skill(skill_name)
        if skill is None:
            return SkillResult(success=False, error=f"Skill {skill_name} not found")

        return await skill.run(self, params)

    def update_state(self, updates: Dict[str, Any]) -> None:
        """Update runtime context state.

        Args:
            updates: State updates dictionary
        """
        # This would update the runtime context
        # Implementation depends on RuntimeContext structure
        pass