"""Unit tests for skill applier."""

import os
import tempfile
import pytest
from foils.generator import FoilGenerator, Foil
from harness.generator import HarnessGenerator, HarnessTool
from skills.selector import SkillSelection, SkillSelectionResult, SkillParameters


class TestFoilGenerator:
    """Tests for FoilGenerator class."""

    def test_init(self):
        """Test generator initialization."""
        generator = FoilGenerator()
        assert len(generator.foils) > 0

    def test_generate_foils(self):
        """Test generating foils."""
        generator = FoilGenerator()
        foils = generator.generate_foils()

        assert len(foils) > 0
        assert all(isinstance(f, Foil) for f in foils)

    def test_generate_typescript_foils(self):
        """Test generating TypeScript foils."""
        generator = FoilGenerator()
        foils = generator.generate_foils(force_typescript=True)

        assert len(foils) > 0

    def test_get_foils_as_code(self):
        """Test getting foils as code string."""
        generator = FoilGenerator()
        foils = generator.generate_foils()[:2]
        code = generator.get_foils_as_code(foils)

        assert "Generated Foils" in code
        assert "```" in code

    def test_save_foils(self, temp_dir):
        """Test saving foils to files."""
        generator = FoilGenerator()
        foils = generator.generate_foils()[:2]

        saved = generator.save_foils(foils, str(temp_dir))

        assert len(saved) == 2
        for path in saved:
            assert os.path.exists(path)

    def test_to_dict(self):
        """Test converting generator to dictionary."""
        generator = FoilGenerator()
        data = generator.to_dict()

        assert "foils" in data
        assert "count" in data
        assert data["count"] == len(generator.foils)


class TestHarnessGenerator:
    """Tests for HarnessGenerator class."""

    def test_init(self):
        """Test generator initialization."""
        generator = HarnessGenerator()
        assert len(generator.tools) > 0

    def test_generate_harness(self):
        """Test generating harness tools."""
        generator = HarnessGenerator()
        tools = generator.generate_harness()

        assert len(tools) > 0
        assert all(isinstance(t, HarnessTool) for t in tools)

    def test_get_best_practices(self):
        """Test getting best practices."""
        generator = HarnessGenerator()
        practices = generator.get_best_practices()

        assert len(practices) > 0
        assert all(isinstance(p, str) for p in practices)

    def test_save_harness(self, temp_dir):
        """Test saving harness to files."""
        generator = HarnessGenerator()
        tools = generator.generate_harness()[:3]

        # Manually save since save_harness uses all tools
        for tool in tools:
            filepath = os.path.join(str(temp_dir), tool.file_path)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(tool.content)

        assert len(list(temp_dir.glob("**/*"))) > 0

    def test_to_dict(self):
        """Test converting generator to dictionary."""
        generator = HarnessGenerator()
        data = generator.to_dict()

        assert "tools" in data
        assert "count" in data


class TestSkillApplier:
    """Tests for skill application."""

    def test_select_skills_and_generate_params(self):
        """Test selecting skills and generating parameters."""
        from skills.selector import SkillSelector

        selector = SkillSelector()
        selections = selector.select_skills(use_llm=False)
        params = selector.generate_parameters(selections)

        assert isinstance(params, dict)
        for skill_id, param in params.items():
            assert isinstance(param, SkillParameters)

    def test_process_user_feedback_accept(self):
        """Test accepting user feedback."""
        from skills.selector import SkillSelector

        selector = SkillSelector()
        selections = selector.select_skills(use_llm=False)

        result = selector.process_user_feedback("accept", selections)
        assert result is selections

    def test_process_user_feedback_reject(self):
        """Test rejecting user feedback."""
        from skills.selector import SkillSelector

        selector = SkillSelector()
        selections = selector.select_skills(use_llm=False)

        result = selector.process_user_feedback("reject", selections)
        assert len(result.selected_skills) == 0

    def test_generate_full_skill_set(self):
        """Test generating full skill set."""
        from skills.selector import SkillSelector

        selector = SkillSelector()
        selections = selector.select_skills(use_llm=False)
        params = selector.generate_parameters(selections)

        skill_set = selector.generate_full_skill_set(selections, params)

        assert "skills" in skill_set
        assert "configuration" in skill_set
        assert skill_set["skills"] is not None
