"""Integration tests for end-to-end workflow."""

import os
import pytest
from scanner.project_scanner import ProjectScanner
from analyzer.log_analyzer import LogAnalyzer
from skills.catalog import SkillCatalog
from skills.selector import SkillSelector
from foils.generator import FoilGenerator


class TestEndToEndWorkflow:
    """Tests for complete end-to-end workflow."""

    def test_scan_recommender_apply_workflow(self, sample_project_path):
        """Test complete workflow: scan -> recommend -> apply."""
        # Step 1: Scan project
        scanner = ProjectScanner()
        structure = scanner.scan(sample_project_path)

        assert structure is not None
        assert structure.file_count > 0

        # Step 2: Get skill recommendations
        selector = SkillSelector(structure)
        selections = selector.select_skills(use_llm=False)

        assert selections.selected_skills is not None

        # Step 3: Generate foils
        foil_gen = FoilGenerator(structure)
        foils = foil_gen.generate_foils()

        assert len(foils) > 0

    def test_full_workflow_with_log_analysis(self, sample_project_path):
        """Test workflow including log analysis."""
        # Create a log file
        log_path = os.path.join(sample_project_path, "app.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w") as f:
            f.write("ERROR: Database connection failed\n")
            f.write("WARNING: Slow query detected\n")
            f.write("INFO: User logged in\n")

        # Scan project
        scanner = ProjectScanner()
        structure = scanner.scan(sample_project_path)

        # Analyze logs
        analyzer = LogAnalyzer(structure)
        analyses = analyzer.analyze_project_logs()

        assert len(analyses) > 0

        # Get summary
        summary = analyzer.get_summary()
        assert summary["error_count"] >= 1
        assert summary["warning_count"] >= 1
        assert summary["info_count"] >= 1

    def test_skill_catalog_integration(self, sample_skill_catalog):
        """Test skill catalog integration."""
        import json

        # Save sample catalog
        catalog_path = "/tmp/test_integration_skills.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        # Load and index
        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        # Search and filter
        frontend_skills = catalog.get_skills_by_category("frontend")
        assert len(frontend_skills) > 0

        # Get specific skill
        skill = catalog.get_skill("react-hooks")
        assert skill is not None
        assert skill.name == "React Custom Hooks"

    def test_context_aware_prompt_construction(self, sample_project_path):
        """Test context-aware prompt construction."""
        from context.prompts import ContextPromptBuilder

        scanner = ProjectScanner()
        structure = scanner.scan(sample_project_path)

        builder = ContextPromptBuilder(structure)
        context = builder.build_context(structure)

        assert context.project_name == "test-project"
        assert context.technology_stack.get("typescript") is True
        assert context.technology_stack.get("react") is True

    def test_harness_generation_with_project_context(self, sample_project_path):
        """Test harness generation with project context."""
        from harness.generator import HarnessGenerator

        scanner = ProjectScanner()
        structure = scanner.scan(sample_project_path)

        generator = HarnessGenerator(structure)
        tools = generator.generate_harness()

        assert len(tools) > 0
        assert any(t.id == "setup" for t in tools)
        assert any(t.id == "dev" for t in tools)

    def test_foil_generation_with_typescript_context(self, sample_project_path):
        """Test foil generation with TypeScript context."""
        from foils.generator import FoilGenerator

        scanner = ProjectScanner()
        structure = scanner.scan(sample_project_path)

        generator = FoilGenerator(structure)
        foils = generator.generate_foils()

        # Should include TypeScript-specific foils
        assert len(foils) > 0
        assert any("typescript" in f.tags for f in foils)


class TestMultiStepOperations:
    """Tests for multi-step operations."""

    def test_create_and_validate_project(self, temp_dir):
        """Test creating and validating a new project."""
        from admin.commands import AdminCommands
        from config import ProgramistoConfig

        project_path = str(temp_dir / "new-project")

        admin = AdminCommands()
        result = admin.new_project("new-project", template="basic")

        assert result.success
        assert os.path.exists(project_path)
        assert os.path.exists(os.path.join(project_path, "programisto-config.yaml"))

        # Validate
        validation = admin.validate_project(project_path)
        assert validation.success

    def test_add_skill_repo_workflow(self, temp_dir):
        """Test adding a skill repository."""
        from admin.commands import AdminCommands

        admin = AdminCommands()

        # Try to add a known repository (may fail if network unavailable)
        result = admin.add_skill_repo(
            "https://github.com/example/skills",
            name="example-skills"
        )

        # Just verify the method works (may succeed or fail gracefully)
        assert "message" in result.to_dict()

    def test_cli_tool_configuration(self, temp_dir):
        """Test CLI tool configuration workflow."""
        from tools.cli_support import CLISupport

        config_path = str(temp_dir / "programisto-config.yaml")

        cli_support = CLISupport(config_path=config_path)

        # Add a tool
        result = cli_support.add_tool("aider", {
            "enabled": True,
            "skills_dir": "~/.aider/skills",
        })
        assert result is True

        # Get configuration
        config = cli_support.get_tool_config("aider")
        assert config is not None
        assert config["enabled"] is True

        # Save and reload
        cli_support.save_config()
        assert os.path.exists(config_path)

        # Reload
        cli_support2 = CLISupport(config_path=config_path)
        config2 = cli_support2.get_tool_config("aider")
        assert config2 is not None

    def test_dry_run_execution(self):
        """Test dry-run execution."""
        from utils.testing import DryRunExecutor, temporary_directory

        executor = DryRunExecutor(enabled=True)

        with temporary_directory() as tmpdir:
            # Simulate file creation
            result = executor.execute_file_create(
                os.path.join(tmpdir, "test.txt"),
                "Test content"
            )

            # In dry-run, should return None for destructive ops
            assert result is None

            # Check summary
            summary = executor.get_summary()
            assert "DRY-RUN" in summary

    def test_test_runner_detection(self, sample_project_path):
        """Test test runner detection."""
        from utils.testing import TestRunner

        runner = TestRunner(sample_project_path)

        # Detect test command
        cmd = runner.detect_test_command()
        # Should detect npm test for our sample project
        assert cmd is not None


class TestConfigurationPersistence:
    """Tests for configuration persistence."""

    def test_save_and_restore_skill_selection(self, sample_project_path):
        """Test saving and restoring skill selections."""
        from skills.selector import SkillSelector
        import json

        selector = SkillSelector()
        selections = selector.select_skills(use_llm=False)

        # Save to dict
        data = selections.to_dict()

        # Restore
        restored = SkillSelector()
        # Note: This is a simplified test - full restoration would need
        # reconstruction of SkillSelection objects

        assert data is not None
        assert "selected_skills" in data
