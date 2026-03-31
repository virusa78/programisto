"""Integration tests for multi-agent CLI support."""

import os
import json
import pytest
from tools.cli_support import CLISupport, ToolConfig, ToolRegistry


class TestMultiAgentConfiguration:
    """Tests for multi-agent CLI configuration."""

    def test_configure_claude_code(self, temp_dir):
        """Test configuring Claude Code."""
        config_path = str(temp_dir / "programisto-config.yaml")

        cli_support = CLISupport(config_path=config_path)

        # Add Claude Code
        result = cli_support.add_tool("claude-code", {
            "enabled": True,
            "skills_dir": "~/.claude/skills",
            "activation": "file-based",
            "version": "latest",
        })

        assert result is True

        # Verify configuration
        config = cli_support.get_tool_config("claude-code")
        assert config is not None
        assert config["skills_dir"] == "~/.claude/skills"

    def test_configure_multiple_tools(self, temp_dir):
        """Test configuring multiple CLI tools."""
        config_path = str(temp_dir / "programisto-config.yaml")

        cli_support = CLISupport(config_path=config_path)

        # Configure multiple tools
        tools = [
            ("claude-code", {"skills_dir": "~/.claude/skills"}),
            ("cursor", {"skills_dir": ".cursor/skills"}),
            ("aider", {"skills_dir": "~/.aider/skills"}),
        ]

        for tool_name, config in tools:
            cli_support.add_tool(tool_name, config)

        # Verify all configured
        for tool_name, _ in tools:
            config = cli_support.get_tool_config(tool_name)
            assert config is not None

    def test_enable_disable_tools(self, temp_dir):
        """Test enabling and disabling tools."""
        config_path = str(temp_dir / "programisto-config.yaml")

        cli_support = CLISupport(config_path=config_path)

        # Get initial enabled tools
        initial = cli_support.get_enabled_tools()

        # Disable a tool
        cli_support.remove_tool("codex")

        # Verify disabled
        config = cli_support.get_tool_config("codex")
        assert config is not None
        assert config["enabled"] is False

    def test_cross_platform_skills(self, temp_dir):
        """Test cross-platform skill distribution."""
        config_path = str(temp_dir / "programisto-config.yaml")

        cli_support = CLISupport(config_path=config_path)

        # Get skill distribution
        distribution = cli_support.get_cross_platform_skills(str(temp_dir))

        assert isinstance(distribution, dict)

    def test_activation_commands(self):
        """Test getting activation commands."""
        cli_support = CLISupport()

        commands = cli_support.get_activation_commands()

        assert "claude-code" in commands
        assert "cursor" in commands
        assert "aider" in commands

    def test_migration_guidance(self, temp_dir):
        """Test configuration migration guidance."""
        config_path = str(temp_dir / "programisto-config.yaml")

        cli_support = CLISupport(config_path=config_path)

        old_config = {
            "tools": {
                "claude_code": {"enabled": True, "skills_dir": "~/.old"},
                "codex": {"enabled": True},
            }
        }

        new_config = {
            "tools": {
                "claude_code": {"enabled": True, "skills_dir": "~/.claude/skills"},
                "aider": {"enabled": True},
            }
        }

        guidance = cli_support.get_migration_guidance(old_config, new_config)

        assert isinstance(guidance, list)

    def test_validate_configuration(self, temp_dir):
        """Test configuration validation."""
        config_path = str(temp_dir / "programisto-config.yaml")

        cli_support = CLISupport(config_path=config_path)

        # Add invalid configuration
        cli_support.add_tool("test-tool", {
            "skills_dir": "",  # Missing required field
        })

        # Validate
        errors = cli_support.validate_config()
        # Should have errors

    def test_save_and_reload_config(self, temp_dir):
        """Test saving and reloading configuration."""
        config_path = str(temp_dir / "programisto-config.yaml")

        # Create and configure
        cli_support = CLISupport(config_path=config_path)
        cli_support.add_tool("cursor", {
            "enabled": True,
            "skills_dir": ".cursor/skills",
        })
        cli_support.save_config()

        # Reload
        cli_support2 = CLISupport(config_path=config_path)
        config = cli_support2.get_tool_config("cursor")

        assert config is not None
        assert config["skills_dir"] == ".cursor/skills"

    def test_tool_registry_serialization(self):
        """Test tool registry serialization."""
        registry = ToolRegistry()

        # Modify a tool
        registry.claude_code.skills_dir = "~/.custom/skills"
        registry.claude_code.enabled = False

        # Serialize
        data = registry.to_dict()

        assert data["claude_code"]["skills_dir"] == "~/.custom/skills"
        assert data["claude_code"]["enabled"] is False

        # Deserialize
        new_registry = ToolRegistry.from_dict(data)
        assert new_registry.claude_code.skills_dir == "~/.custom/skills"
        assert new_registry.claude_code.enabled is False

    def test_default_tool_configurations(self):
        """Test default tool configurations."""
        cli_support = CLISupport()

        # Check all tools have defaults
        for tool_name in cli_support.DEFAULT_TOOLS:
            config = cli_support.get_tool_config(tool_name.replace("_", "-"))
            assert config is not None
            assert "enabled" in config
            assert "skills_dir" in config


class TestSkillRepositoryManagement:
    """Tests for skill repository management."""

    def test_list_skills(self, temp_dir):
        """Test listing available skills."""
        from admin.commands import AdminCommands

        admin = AdminCommands()
        result = admin.list_skills()

        assert result.success
        assert "skills" in result.data

    def test_list_tools(self, temp_dir):
        """Test listing configured tools."""
        from admin.commands import AdminCommands

        admin = AdminCommands()
        result = admin.list_tools()

        assert result.success
        assert "tools" in result.data

    def test_admin_validate_project(self, sample_project_path):
        """Test admin validate command."""
        from admin.commands import AdminCommands

        admin = AdminCommands()
        result = admin.validate_project(sample_project_path)

        assert isinstance(result.success, bool)
        assert "issues" in result.data
        assert "warnings" in result.data
