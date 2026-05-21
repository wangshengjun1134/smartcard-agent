"""Skill Registry for managing and discovering skills.

This module provides the SkillRegistry class for registering
and retrieving skills by name.
"""

from typing import Dict, List, Optional, Any, Type
from skills.base.base_skill import BaseSkill


class SkillRegistry:
    """Registry for skill management.

    Provides:
    - Skill registration
    - Skill retrieval by name
    - Skill discovery by category or capability
    - Skill validation

    Example:
        registry = SkillRegistry()
        registry.register(SelectFileSkill())
        registry.register(ReadImsiSkill())

        skill = registry.get_skill("select_file")
        result = await skill.run(ctx, {"fid": "3F00"})
    """

    def __init__(self):
        """Initialize skill registry."""
        self._skills: Dict[str, BaseSkill] = {}
        self._categories: Dict[str, List[str]] = {
            "primitive": [],
            "composite": [],
            "exploratory": [],
            "workflow": [],
        }

    def register(self, skill: BaseSkill, category: str = "primitive") -> None:
        """Register a skill.

        Args:
            skill: Skill instance to register
            category: Skill category (primitive, composite, exploratory, workflow)

        Raises:
            ValueError: If skill name already registered or category invalid.
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill {skill.name} already registered")

        if category not in self._categories:
            raise ValueError(f"Invalid category: {category}")

        self._skills[skill.name] = skill
        self._categories[category].append(skill.name)

    def unregister(self, skill_name: str) -> bool:
        """Unregister a skill.

        Args:
            skill_name: Name of skill to unregister

        Returns:
            True if unregistered, False if not found.
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
            # Remove from all categories
            for cat_skills in self._categories.values():
                if skill_name in cat_skills:
                    cat_skills.remove(skill_name)
            return True
        return False

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name.

        Args:
            skill_name: Name of skill to retrieve

        Returns:
            Skill instance or None if not found.
        """
        return self._skills.get(skill_name)

    def has_skill(self, skill_name: str) -> bool:
        """Check if skill is registered.

        Args:
            skill_name: Skill name

        Returns:
            True if registered.
        """
        return skill_name in self._skills

    def list_skills(self) -> List[str]:
        """List all registered skill names.

        Returns:
            List of skill names.
        """
        return list(self._skills.keys())

    def list_skills_by_category(self, category: str) -> List[str]:
        """List skills in a category.

        Args:
            category: Category name

        Returns:
            List of skill names in category.
        """
        return self._categories.get(category, [])

    def list_categories(self) -> List[str]:
        """List all categories.

        Returns:
            List of category names.
        """
        return list(self._categories.keys())

    def find_skills_by_capability(self, capability: str) -> List[str]:
        """Find skills that require a capability.

        Args:
            capability: Capability name

        Returns:
            List of skill names requiring the capability.
        """
        result = []
        for name, skill in self._skills.items():
            if capability in skill.required_capabilities:
                result.append(name)
        return result

    def find_skills_for_card_type(self, card_type: str) -> List[str]:
        """Find skills that support a card type.

        Args:
            card_type: Card type name

        Returns:
            List of skill names supporting the card type.
        """
        result = []
        for name, skill in self._skills.items():
            # Empty supported_card_types means all cards
            if not skill.supported_card_types or card_type in skill.supported_card_types:
                result.append(name)
        return result

    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get metadata for all registered skills.

        Returns:
            Dictionary of skill name -> metadata.
        """
        return {
            name: skill.get_metadata()
            for name, skill in self._skills.items()
        }

    def get_dangerous_skills(self) -> List[str]:
        """Get list of dangerous skills.

        Returns:
            List of skill names marked as dangerous.
        """
        return [
            name for name, skill in self._skills.items()
            if skill.dangerous
        ]

    def get_skills_requiring_pin(self) -> List[str]:
        """Get list of skills requiring PIN.

        Returns:
            List of skill names requiring PIN verification.
        """
        return [
            name for name, skill in self._skills.items()
            if skill.requires_pin
        ]

    def get_skills_requiring_secure_channel(self) -> List[str]:
        """Get list of skills requiring secure channel.

        Returns:
            List of skill names requiring secure channel.
        """
        return [
            name for name, skill in self._skills.items()
            if skill.requires_secure_channel
        ]

    def validate_skill_for_context(
        self,
        skill_name: str,
        ctx: Any,
    ) -> tuple[bool, str]:
        """Validate if skill can be executed in given context.

        Args:
            skill_name: Skill name to validate
            ctx: Runtime context

        Returns:
            Tuple of (can_execute, reason_if_not)
        """
        skill = self.get_skill(skill_name)
        if skill is None:
            return False, f"Skill {skill_name} not found"

        return skill.can_execute(ctx)

    def clear(self) -> None:
        """Clear all registered skills."""
        self._skills.clear()
        for category in self._categories:
            self._categories[category] = []


# Global skill registry instance
_global_registry: Optional[SkillRegistry] = None


def get_registry() -> SkillRegistry:
    """Get the global skill registry.

    Returns:
        Global SkillRegistry instance.
    """
    if _global_registry is None:
        _global_registry = SkillRegistry()
    return _global_registry


def register(skill: BaseSkill, category: str = "primitive") -> None:
    """Register a skill in the global registry.

    Args:
        skill: Skill to register
        category: Skill category
    """
    get_registry().register(skill, category)


def get_skill(name: str) -> Optional[BaseSkill]:
    """Get a skill from the global registry.

    Args:
        name: Skill name

    Returns:
        Skill instance or None.
    """
    return get_registry().get_skill(name)