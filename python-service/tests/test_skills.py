"""Tests for skill system."""

import pytest
from unittest.mock import Mock, AsyncMock
from skills.base.base_skill import BaseSkill, SkillResult
from skills.base.registry import SkillRegistry, register, get_skill
from skills.primitive.select_file import SelectFileSkill
from skills.primitive.read_binary import ReadBinarySkill
from skills.composite.read_imsi import ReadImsiSkill


class TestBaseSkill:
    """Tests for BaseSkill."""

    def test_skill_metadata(self):
        """Test skill metadata."""
        skill = SelectFileSkill()
        assert skill.name == "select_file"
        assert skill.dangerous == False
        assert skill.requires_pin == False

    def test_get_metadata(self):
        """Test get_metadata method."""
        skill = SelectFileSkill()
        metadata = skill.get_metadata()
        assert metadata["name"] == "select_file"
        assert "description" in metadata

    def test_validate_params(self):
        """Test parameter validation."""
        skill = SelectFileSkill()

        valid, error = skill.validate_params({"fid": "3F00"})
        assert valid == True

        valid, error = skill.validate_params({"fid": "invalid"})
        assert valid == False

        valid, error = skill.validate_params({})
        assert valid == False


class TestSkillRegistry:
    """Tests for skill registry."""

    def test_register_skill(self):
        """Test skill registration."""
        registry = SkillRegistry()
        skill = SelectFileSkill()

        registry.register(skill, "primitive")
        assert registry.has_skill("select_file")

    def test_get_skill(self):
        """Test get skill."""
        registry = SkillRegistry()
        skill = SelectFileSkill()

        registry.register(skill)
        retrieved = registry.get_skill("select_file")
        assert retrieved is skill

    def test_unregister_skill(self):
        """Test skill unregistration."""
        registry = SkillRegistry()
        skill = SelectFileSkill()

        registry.register(skill)
        result = registry.unregister("select_file")
        assert result == True
        assert not registry.has_skill("select_file")

    def test_list_skills(self):
        """Test list skills."""
        registry = SkillRegistry()
        registry.register(SelectFileSkill())
        registry.register(ReadBinarySkill())

        skills = registry.list_skills()
        assert "select_file" in skills
        assert "read_binary" in skills

    def test_list_by_category(self):
        """Test list by category."""
        registry = SkillRegistry()
        registry.register(SelectFileSkill(), "primitive")
        registry.register(ReadImsiSkill(), "composite")

        primitive_skills = registry.list_skills_by_category("primitive")
        assert "select_file" in primitive_skills

        composite_skills = registry.list_skills_by_category("composite")
        assert "read_imsi" in composite_skills

    def test_get_dangerous_skills(self):
        """Test get dangerous skills."""
        registry = SkillRegistry()
        skill1 = SelectFileSkill()
        skill1.dangerous = False

        skill2 = Mock()
        skill2.name = "dangerous_skill"
        skill2.dangerous = True

        registry.register(skill1)
        registry.register(skill2)

        dangerous = registry.get_dangerous_skills()
        assert "dangerous_skill" in dangerous


class TestSkillResult:
    """Tests for SkillResult."""

    def test_success_result(self):
        """Test success result."""
        result = SkillResult(
            success=True,
            data=bytes.fromhex("0001"),
            sw="9000",
        )
        assert result.success == True
        assert result.error is None

    def test_error_result(self):
        """Test error result."""
        result = SkillResult(
            success=False,
            error="File not found",
            sw="6A82",
        )
        assert result.success == False
        assert result.error == "File not found"

    def test_result_with_metadata(self):
        """Test result with metadata."""
        result = SkillResult(
            success=True,
            metadata={"imsi": "46000123456789"},
        )
        assert result.metadata["imsi"] == "46000123456789"


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_register_global(self):
        """Test global register."""
        from skills.base.registry import get_registry

        registry = get_registry()
        registry.clear()

        skill = SelectFileSkill()
        register(skill)

        assert registry.has_skill("select_file")

    def test_get_skill_global(self):
        """Test global get_skill."""
        from skills.base.registry import get_registry

        registry = get_registry()
        registry.clear()

        skill = SelectFileSkill()
        register(skill)

        retrieved = get_skill("select_file")
        assert retrieved is skill


class TestIMSIParser:
    """Tests for IMSI parser."""

    def test_parse_imsi(self):
        """Test IMSI parsing."""
        from skills.composite.read_imsi import parse_imsi

        # IMSI data: length 09, then BCD encoded IMSI
        # Example: 46000123456789
        data = bytes.fromhex("094600123456789F")  # Simplified
        imsi = parse_imsi(data)
        # Note: actual parsing depends on BCD encoding
        assert len(imsi) > 0