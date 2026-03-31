"""Configuration management for Programisto."""

import os
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any, List


@dataclass
class ToolConfig:
    """Configuration for a CLI tool."""
    enabled: bool = True
    skills_dir: str = "~/.programisto/skills"
    activation: str = "file-based"
    version: str = "latest"


@dataclass
class LLMConfig:
    """Configuration for external LLM."""
    enabled: bool = True
    api_key: Optional[str] = None
    base_url: str = "https://192.168.1.10:8088/v1"
    model: str = "claude-3-sonnet-20240229"
    timeout: int = 120


@dataclass
class ProjectConfig:
    """Configuration for a configured CLI tool."""
    claude_code: ToolConfig = field(default_factory=ToolConfig)
    codex: ToolConfig = field(default_factory=ToolConfig)
    cursor: ToolConfig = field(default_factory=ToolConfig)
    gemini: ToolConfig = field(default_factory=ToolConfig)
    openclaw: ToolConfig = field(default_factory=ToolConfig)
    vscode: ToolConfig = field(default_factory=ToolConfig)
    copilot: ToolConfig = field(default_factory=ToolConfig)
    goose: ToolConfig = field(default_factory=ToolConfig)
    opencode: ToolConfig = field(default_factory=ToolConfig)
    aider: ToolConfig = field(default_factory=ToolConfig)
    windsurf: ToolConfig = field(default_factory=ToolConfig)
    kilo: ToolConfig = field(default_factory=ToolConfig)
    augment: ToolConfig = field(default_factory=ToolConfig)
    antigravity: ToolConfig = field(default_factory=ToolConfig)


@dataclass
class ProgramistoConfig:
    """Main configuration for Programisto."""
    project_dir: Optional[str] = None
    llm: LLMConfig = field(default_factory=LLMConfig)
    tools: ProjectConfig = field(default_factory=ProjectConfig)
    dry_run: bool = False
    verbose: bool = False
    skill_index_path: str = "skills_catalog/skills_index.json"

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "ProgramistoConfig":
        """Load configuration from file or create default."""
        if config_path is None:
            # Look for config in common locations
            possible_paths = [
                "programisto-config.yaml",
                "~/.programisto/config.yaml",
                os.path.expanduser("~/.programisto/config.yaml"),
            ]
            for path in possible_paths:
                expanded = os.path.expanduser(path)
                if os.path.exists(expanded):
                    config_path = expanded
                    break

        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
            return cls._from_dict(data)
        return cls()

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "ProgramistoConfig":
        """Create config from dictionary."""
        config = cls()

        if "project_dir" in data:
            config.project_dir = data["project_dir"]

        if "llm" in data:
            config.llm = LLMConfig(**data["llm"])

        if "tools" in data:
            tools_data = data["tools"]
            for tool_name in dir(config.tools):
                if tool_name.startswith("_"):
                    continue
                if tool_name in tools_data:
                    setattr(
                        config.tools,
                        tool_name,
                        ToolConfig(**tools_data[tool_name]),
                    )

        if "dry_run" in data:
            config.dry_run = data["dry_run"]

        if "verbose" in data:
            config.verbose = data["verbose"]

        if "skill_index_path" in data:
            config.skill_index_path = data["skill_index_path"]

        return config

    def save(self, config_path: str = "programisto-config.yaml") -> None:
        """Save configuration to file."""
        data = asdict(self)
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tool names."""
        enabled = []
        for tool_name in dir(self.tools):
            if tool_name.startswith("_"):
                continue
            tool = getattr(self.tools, tool_name)
            if isinstance(tool, ToolConfig) and tool.enabled:
                enabled.append(tool_name)
        return enabled


# Global config instance
_config: Optional[ProgramistoConfig] = None


def get_config() -> ProgramistoConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = ProgramistoConfig.load()
    return _config


def reload_config() -> ProgramistoConfig:
    """Reload configuration from file."""
    global _config
    _config = ProgramistoConfig.load()
    return _config


def save_config(config: ProgramistoConfig, path: Optional[str] = None) -> None:
    """Save the configuration."""
    path = path or "programisto-config.yaml"
    config.save(path)
    global _config
    _config = config
