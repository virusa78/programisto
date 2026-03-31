"""Unit tests for config generator."""

import os
import json
import pytest
from config import ProgramistoConfig, LLMConfig, ToolConfig, get_config, save_config


class TestProgramistoConfig:
    """Tests for ProgramistoConfig class."""

    def test_init_defaults(self):
        """Test default configuration values."""
        config = ProgramistoConfig()

        assert config.project_dir is None
        assert config.dry_run is False
        assert config.verbose is False
        assert config.llm is not None

    def test_init_with_values(self):
        """Test configuration with custom values."""
        config = ProgramistoConfig(
            project_dir="/test/project",
            dry_run=True,
            verbose=True,
        )

        assert config.project_dir == "/test/project"
        assert config.dry_run is True
        assert config.verbose is True

    def test_save_and_load(self, temp_dir):
        """Test saving and loading configuration."""
        config_path = temp_dir / "config.yaml"
        config = ProgramistoConfig(
            project_dir="/test",
            dry_run=True,
        )
        config.save(str(config_path))

        # Reload
        loaded = ProgramistoConfig.load(str(config_path))
        assert loaded.project_dir == "/test"
        assert loaded.dry_run is True

    def test_get_enabled_tools(self):
        """Test getting enabled tools."""
        config = ProgramistoConfig()
        enabled = config.get_enabled_tools()

        assert len(enabled) > 0
        # Check for any enabled tool (name may vary)
        assert any("claude" in t.lower() for t in enabled)


class TestLLMConfig:
    """Tests for LLMConfig class."""

    def test_init_defaults(self):
        """Test default LLM config values."""
        config = LLMConfig()

        assert config.enabled is True
        assert config.api_key is None
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "claude-3-sonnet-20240229"
        assert config.timeout == 120

    def test_init_with_values(self):
        """Test LLM config with custom values."""
        config = LLMConfig(
            api_key="test-key",
            base_url="https://custom.api.com",
            model="custom-model",
            timeout=60,
        )

        assert config.api_key == "test-key"
        assert config.base_url == "https://custom.api.com"
        assert config.timeout == 60


class TestToolConfig:
    """Tests for ToolConfig class."""

    def test_init_defaults(self):
        """Test default tool config values."""
        config = ToolConfig()

        assert config.enabled is True
        assert config.skills_dir == "~/.programisto/skills"
        assert config.activation == "file-based"
        assert config.version == "latest"

    def test_init_with_values(self):
        """Test tool config with custom values."""
        config = ToolConfig(
            enabled=False,
            skills_dir="/custom/path",
            activation="yaml-frontmatter",
            version="1.0.0",
        )

        assert config.enabled is False
        assert config.skills_dir == "/custom/path"
        assert config.activation == "yaml-frontmatter"


class TestConfigFunctions:
    """Tests for config module functions."""

    def test_get_config(self):
        """Test getting global config."""
        config = get_config()
        assert isinstance(config, ProgramistoConfig)

    def test_reload_config(self, temp_dir):
        """Test reloading configuration."""
        # Create a config file
        config_path = temp_dir / "config.yaml"
        config = ProgramistoConfig(project_dir="/test")
        config.save(str(config_path))

        # Load and verify
        loaded = ProgramistoConfig.load(str(config_path))
        assert loaded.project_dir == "/test"

    def test_save_config(self, temp_dir):
        """Test saving configuration."""
        config_path = temp_dir / "config.yaml"
        config = ProgramistoConfig(project_dir="/test")
        save_config(config, str(config_path))

        assert config_path.exists()

        # Verify content
        with open(config_path) as f:
            content = f.read()
        assert "project_dir" in content


class TestConfigParsing:
    """Tests for configuration parsing."""

    def test_parse_yaml_config(self, temp_dir):
        """Test parsing YAML configuration."""
        config_path = temp_dir / "config.yaml"
        config_path.write_text("""
project_dir: /my/project
llm:
  enabled: true
  api_key: test-key
  base_url: https://api.example.com
  model: test-model
  timeout: 60
tools:
  claude-code:
    enabled: true
    skills_dir: ~/.claude/skills
    activation: file-based
""")

        loaded = ProgramistoConfig.load(str(config_path))
        assert loaded.project_dir == "/my/project"
        assert loaded.llm.api_key == "test-key"
        assert loaded.llm.timeout == 60

    def test_parse_partial_config(self, temp_dir):
        """Test parsing partial configuration."""
        config_path = temp_dir / "config.yaml"
        config_path.write_text("""
project_dir: /test
""")

        loaded = ProgramistoConfig.load(str(config_path))
        assert loaded.project_dir == "/test"
        # Other fields should have defaults
        assert loaded.llm.base_url == "https://api.openai.com/v1"
