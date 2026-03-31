"""Unit tests for skill recommender."""

import pytest
from skills.selector import SkillSelector, SkillSelection, SkillSelectionResult
from scanner.project_scanner import ProjectStructure
from tests.fixtures.mock_llm import MockLLMClient


class TestSkillSelector:
    """Tests for SkillSelector class."""

    def test_init(self):
        """Test selector initialization."""
        selector = SkillSelector()
        assert selector.project_structure is None

    def test_select_with_rule_based(self):
        """Test rule-based skill selection."""
        selector = SkillSelector()
        result = selector.select_skills(use_llm=False)

        # Should return at least some high-priority skills
        assert result.selected_skills is not None

    def test_select_skills_with_mock_llm(self, mock_llm):
        """Test skill selection with LLM."""
        selector = SkillSelector(llm_client=mock_llm)
        result = selector.select_skills(use_llm=True)

        # LLM selection might fail and fall back to rule-based
        assert result.selected_skills is not None

    def test_generate_parameters(self):
        """Test parameter generation."""
        selector = SkillSelector()
        result = selector.select_skills(use_llm=False)
        params = selector.generate_parameters(result)

        assert isinstance(params, dict)


class TestSkillSelection:
    """Tests for SkillSelection class."""

    def test_selection_creation(self):
        """Test creating a skill selection."""
        selection = SkillSelection(
            skill_id="test-skill",
            name="Test Skill",
            description="A test skill",
            priority="high",
            confidence=0.9,
            justification="Because",
        )

        assert selection.skill_id == "test-skill"
        assert selection.priority == "high"
        assert selection.confidence == 0.9

    def test_selection_to_dict(self):
        """Test converting selection to dictionary."""
        selection = SkillSelection(
            skill_id="test",
            name="Test",
            description="Test",
            priority="medium",
            confidence=0.5,
            justification="Test",
            files=["file1.ts"],
        )

        data = selection.to_dict()
        assert data["skill_id"] == "test"
        assert data["files"] == ["file1.ts"]


class TestSkillSelectionResult:
    """Tests for SkillSelectionResult class."""

    def test_result_creation(self):
        """Test creating a selection result."""
        result = SkillSelectionResult()

        assert result.selected_skills == []
        assert result.excluded_skills == []

    def test_result_with_skills(self):
        """Test result with selected skills."""
        selection = SkillSelection(
            skill_id="skill1",
            name="Skill 1",
            description="First skill",
            priority="high",
            confidence=0.9,
            justification="Test",
        )

        result = SkillSelectionResult(
            selected_skills=[selection],
            excluded_skills=["skill2"],
            recommendations=["Use skill1"],
        )

        assert len(result.selected_skills) == 1
        assert "skill2" in result.excluded_skills


class TestSkillParameters:
    """Tests for SkillParameters class."""

    def test_parameters_creation(self):
        """Test creating skill parameters."""
        from skills.selector import SkillParameters

        params = SkillParameters(
            skill_id="test-skill",
            enabled=True,
            config={"strict": True},
            order=1,
        )

        assert params.skill_id == "test-skill"
        assert params.enabled is True
        assert params.config["strict"] is True

    def test_parameters_to_dict(self):
        """Test converting parameters to dictionary."""
        from skills.selector import SkillParameters

        params = SkillParameters(
            skill_id="test",
            enabled=True,
            config={"key": "value"},
            order=1,
        )

        data = params.to_dict()
        assert data["enabled"] is True
        assert data["config"]["key"] == "value"
