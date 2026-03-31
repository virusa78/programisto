"""CLI tool support for Programisto.

Requirement 15: Multi-Agent CLI Tool Support

Supports configuration for multiple AI coding CLI tools with YAML configuration.
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class ToolConfig:
    """Configuration for a CLI tool."""

    enabled: bool = True
    skills_dir: str = "~/.programisto/skills"
    activation: str = "file-based"
    version: str = "latest"
    installation_path: Optional[str] = None
    config_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolRegistry:
    """Registry of supported CLI tools."""

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claude_code": self.claude_code.to_dict(),
            "codex": self.codex.to_dict(),
            "cursor": self.cursor.to_dict(),
            "gemini": self.gemini.to_dict(),
            "openclaw": self.openclaw.to_dict(),
            "vscode": self.vscode.to_dict(),
            "copilot": self.copilot.to_dict(),
            "goose": self.goose.to_dict(),
            "opencode": self.opencode.to_dict(),
            "aider": self.aider.to_dict(),
            "windsurf": self.windsurf.to_dict(),
            "kilo": self.kilo.to_dict(),
            "augment": self.augment.to_dict(),
            "antigravity": self.antigravity.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolRegistry":
        """Create ToolRegistry from dictionary."""
        registry = cls()

        tool_map = {
            "claude_code": "claude_code",
            "codex": "codex",
            "cursor": "cursor",
            "gemini": "gemini",
            "openclaw": "openclaw",
            "vscode": "vscode",
            "copilot": "copilot",
            "goose": "goose",
            "opencode": "opencode",
            "aider": "aider",
            "windsurf": "windsurf",
            "kilo": "kilo",
            "augment": "augment",
            "antigravity": "antigravity",
        }

        for config_key, attr_name in tool_map.items():
            if config_key in data:
                setattr(
                    registry,
                    attr_name,
                    ToolConfig(**data[config_key]),
                )

        return registry


class CLISupport:
    """Multi-agent CLI tool support."""

    # Default tool configurations
    DEFAULT_TOOLS = {
        "claude-code": {
            "enabled": True,
            "skills_dir": "~/.claude/skills",
            "activation": "file-based",
            "version": "latest",
        },
        "codex": {
            "enabled": True,
            "skills_dir": "~/.codex/skills",
            "activation": "yaml-frontmatter",
            "version": "latest",
        },
        "cursor": {
            "enabled": True,
            "skills_dir": ".cursor/skills",
            "activation": "project-local",
            "version": "latest",
        },
        "gemini": {
            "enabled": True,
            "skills_dir": ".gemini/skills",
            "activation": "activate_skill()",
            "version": "latest",
        },
        "openclaw": {
            "enabled": True,
            "skills_dir": "~/.openclaw/skills",
            "activation": "yaml-frontmatter-triggers",
            "version": "latest",
        },
        "vscode": {
            "enabled": True,
            "skills_dir": "~/.vscode/skills",
            "activation": "extension",
            "version": "latest",
        },
        "copilot": {
            "enabled": True,
            "skills_dir": "~/.copilot/skills",
            "activation": "extension",
            "version": "latest",
        },
        "goose": {
            "enabled": True,
            "skills_dir": "~/.goose/skills",
            "activation": "file-based",
            "version": "latest",
        },
        "opencode": {
            "enabled": True,
            "skills_dir": "~/.opencode/skills",
            "activation": "file-based",
            "version": "latest",
        },
        "aider": {
            "enabled": True,
            "skills_dir": "~/.aider/skills",
            "activation": "file-based",
            "version": "latest",
        },
        "windsurf": {
            "enabled": True,
            "skills_dir": "~/.windsurf/skills",
            "activation": "extension",
            "version": "latest",
        },
        "kilo": {
            "enabled": True,
            "skills_dir": "~/.kilo/skills",
            "activation": "file-based",
            "version": "latest",
        },
        "augment": {
            "enabled": True,
            "skills_dir": "~/.augment/skills",
            "activation": "file-based",
            "version": "latest",
        },
        "antigravity": {
            "enabled": True,
            "skills_dir": "~/.antigravity/skills",
            "activation": "file-based",
            "version": "latest",
        },
    }

    def __init__(self, config_path: str = "programisto-config.yaml"):
        """Initialize CLI support.

        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = config_path
        self.registry = ToolRegistry()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            # Initialize with defaults
            return

        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f) or {}

            if "tools" in data:
                self.registry = ToolRegistry.from_dict(data["tools"])

        except (yaml.YAMLError, KeyError) as e:
            print(f"Failed to load config: {e}")

    def save_config(self) -> None:
        """Save configuration to file."""
        data = {
            "version": "1.0.0",
            "tools": self.registry.to_dict(),
        }

        with open(self.config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def add_tool(
        self,
        tool_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add or update a tool configuration.

        Args:
            tool_name: Name of the tool (e.g., "claude-code", "cursor").
            config: Optional configuration overrides.

        Returns:
            True if successful, False if tool not recognized.
        """
        # Normalize tool name
        tool_name = tool_name.lower().replace("-", "_")

        # Check if tool is recognized
        if tool_name not in self.DEFAULT_TOOLS:
            # Try to find a matching tool
            matching = self._find_matching_tool(tool_name)
            if matching:
                tool_name = matching
            else:
                return False

        # Apply configuration
        default_config = self.DEFAULT_TOOLS.get(
            tool_name.replace("_", "-"), {}
        )

        if config:
            default_config.update(config)

        # Set in registry
        setattr(self.registry, tool_name, ToolConfig(**default_config))

        return True

    def _find_matching_tool(self, name: str) -> Optional[str]:
        """Find a matching tool for a given name."""
        name_lower = name.lower()

        for key in self.DEFAULT_TOOLS:
            if key in name_lower or name_lower in key:
                return key

        return None

    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool configuration.

        Args:
            tool_name: Name of the tool.

        Returns:
            True if removed, False if not found.
        """
        tool_name = tool_name.lower().replace("-", "_")

        if hasattr(self.registry, tool_name):
            tool = getattr(self.registry, tool_name)
            tool.enabled = False
            return True

        return False

    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tool names."""
        enabled = []

        for attr_name in dir(self.registry):
            if attr_name.startswith("_"):
                continue

            tool = getattr(self.registry, attr_name)
            if isinstance(tool, ToolConfig) and tool.enabled:
                # Convert back to hyphenated name
                enabled.append(attr_name.replace("_", "-"))

        return enabled

    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific tool.

        Args:
            tool_name: Name of the tool.

        Returns:
            Tool configuration dictionary, or None if not found.
        """
        tool_name = tool_name.lower().replace("-", "_")

        if hasattr(self.registry, tool_name):
            return getattr(self.registry, tool_name).to_dict()

        return None

    def generate_config_file(self, output_path: Optional[str] = None) -> str:
        """Generate a YAML configuration file.

        Args:
            output_path: Optional output path. Defaults to config_path.

        Returns:
            Path to generated config file.
        """
        output_path = output_path or self.config_path

        self.save_config()
        return output_path

    def validate_config(self) -> List[str]:
        """Validate the configuration.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        for attr_name in dir(self.registry):
            if attr_name.startswith("_"):
                continue

            tool = getattr(self.registry, attr_name)
            if not isinstance(tool, ToolConfig):
                continue

            # Validate skills_dir
            if not tool.skills_dir:
                errors.append(
                    f"Tool '{attr_name}': skills_dir is required"
                )

            # Validate activation
            valid_activations = [
                "file-based",
                "yaml-frontmatter",
                "yaml-frontmatter-triggers",
                "activate_skill()",
                "project-local",
                "extension",
            ]
            if tool.activation not in valid_activations:
                errors.append(
                    f"Tool '{attr_name}': invalid activation method '{tool.activation}'"
                )

        return errors

    def get_migration_guidance(
        self,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
    ) -> List[str]:
        """Get migration guidance for configuration changes.

        Args:
            old_config: Previous configuration.
            new_config: New configuration.

        Returns:
            List of migration steps.
        """
        guidance = []

        # Compare tools
        old_tools = set(old_config.get("tools", {}).keys())
        new_tools = set(new_config.get("tools", {}).keys())

        # Removed tools
        removed = old_tools - new_tools
        if removed:
            guidance.append(
                f"Tools removed: {', '.join(removed)}. "
                "These tools will no longer be configured."
            )

        # Added tools
        added = new_tools - old_tools
        if added:
            guidance.append(
                f"New tools added: {', '.join(added)}. "
                "Review and update these configurations as needed."
            )

        # Changed settings
        for tool in old_tools & new_tools:
            old_settings = old_config["tools"].get(tool, {})
            new_settings = new_config["tools"].get(tool, {})

            changed = set(old_settings.keys()) - set(new_settings.keys())
            if changed:
                guidance.append(
                    f"Tool '{tool}': Settings changed: {', '.join(changed)}"
                )

        return guidance

    def get_cross_platform_skills(
        self,
        output_dir: str = "skills/",
    ) -> Dict[str, List[str]]:
        """Get skills distribution for cross-platform support.

        Args:
            output_dir: Base directory for skills.

        Returns:
            Dictionary mapping tool names to their skill files.
        """
        distribution: Dict[str, List[str]] = {}

        # Get enabled tools
        enabled_tools = self.get_enabled_tools()

        for tool in enabled_tools:
            tool_key = tool.replace("-", "_")
            config = self.get_tool_config(tool)

            if config:
                skills_dir = config.get("skills_dir", f"skills/{tool}")
                distribution[tool] = [
                    f"{skills_dir}/skill-1.yaml",
                    f"{skills_dir}/skill-2.yaml",
                ]

        return distribution

    def get_activation_commands(self) -> Dict[str, str]:
        """Get activation commands for each tool.

        Returns:
            Dictionary mapping tool names to activation commands.
        """
        return {
            "claude-code": "No activation needed - file-based",
            "codex": "Add YAML frontmatter to files",
            "cursor": "No activation needed - project-local",
            "gemini": "Call activate_skill() in code",
            "openclaw": "Add YAML frontmatter triggers",
            "vscode": "Extension activates automatically",
            "copilot": "Extension activates automatically",
            "goose": "No activation needed - file-based",
            "opencode": "No activation needed - file-based",
            "aider": "No activation needed - file-based",
            "windsurf": "Extension activates automatically",
            "kilo": "No activation needed - file-based",
            "augment": "No activation needed - file-based",
            "antigravity": "No activation needed - file-based",
        }


# Global CLI support instance
_cli_support: Optional[CLISupport] = None


def get_cli_support(config_path: Optional[str] = None) -> CLISupport:
    """Get or create the global CLI support instance.

    Args:
        config_path: Optional config path.

    Returns:
        CLISupport instance.
    """
    global _cli_support

    if _cli_support is None:
        _cli_support = CLISupport(config_path or "programisto-config.yaml")

    return _cli_support
