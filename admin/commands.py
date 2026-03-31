"""Admin commands for Programisto.

Requirement 16: Admin Commands

Provides admin commands for managing skills, CLI tools, and projects:
- admin add-skill-repo <url>
- admin add-cli <cli-name>
- admin new-project <project-name>
"""

import os
import subprocess
import shutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from tools.cli_support import CLISupport, get_cli_support
from skills.catalog import SkillCatalog, get_catalog
from config import ProgramistoConfig, save_config


@dataclass
class AdminResult:
    """Result of an admin command."""

    success: bool
    message: str
    data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data or {},
        }


class AdminCommands:
    """Admin command implementations."""

    def __init__(self, config: Optional[ProgramistoConfig] = None):
        """Initialize admin commands.

        Args:
            config: Optional configuration.
        """
        self.config = config
        self.cli_support = get_cli_support()
        self.catalog = get_catalog()

    def add_skill_repo(
        self,
        url: str,
        name: Optional[str] = None,
    ) -> AdminResult:
        """Add a new skill repository to index.

        Args:
            url: URL of the skill repository.
            name: Optional name for the repository.

        Returns:
            AdminResult with status.
        """
        # Validate URL
        if not self._is_valid_url(url):
            return AdminResult(
                success=False,
                message=f"Invalid URL: {url}",
            )

        repo_name = name or self._extract_repo_name(url)

        try:
            # Clone or reference the repository
            clone_dir = self._clone_or_reference_repo(url, repo_name)

            # Index skills from the repository
            skills_indexed = self._index_repo_skills(clone_dir)

            # Update skill catalog index
            self.catalog.refresh()

            return AdminResult(
                success=True,
                message=f"Successfully added skill repository '{repo_name}'. "
                        f"Indexed {skills_indexed} skills.",
                data={
                    "repo_name": repo_name,
                    "clone_dir": clone_dir,
                    "skills_indexed": skills_indexed,
                },
            )

        except Exception as e:
            return AdminResult(
                success=False,
                message=f"Failed to add skill repository: {e}",
            )

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        return (
            url.startswith("http://")
            or url.startswith("https://")
            or url.startswith("git@")
        )

    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL."""
        # Handle GitHub URLs
        if "github.com" in url:
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                repo = parts[-1]
                return repo.replace(".git", "")

        # Fallback to URL basename
        return url.split("/")[-1].replace(".git", "")

    def _clone_or_reference_repo(
        self,
        url: str,
        name: str,
    ) -> str:
        """Clone or reference a repository."""
        # Use programisto's internal storage
        storage_dir = ".programisto/repos"
        os.makedirs(storage_dir, exist_ok=True)

        repo_dir = os.path.join(storage_dir, name)

        # Check if already cloned
        if os.path.exists(repo_dir):
            # Update existing clone
            try:
                subprocess.run(
                    ["git", "pull"],
                    cwd=repo_dir,
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                # Remove and reclone
                shutil.rmtree(repo_dir)
                return self._do_clone(url, name, storage_dir)

        return self._do_clone(url, name, storage_dir)

    def _do_clone(self, url: str, name: str, storage_dir: str) -> str:
        """Perform the actual git clone."""
        repo_dir = os.path.join(storage_dir, name)

        try:
            subprocess.run(
                ["git", "clone", url, repo_dir],
                check=True,
                capture_output=True,
            )
            return repo_dir
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}")

    def _index_repo_skills(self, repo_dir: str) -> int:
        """Index skills from a repository."""
        # Look for skills in common locations
        skill_locations = [
            "skills",
            "skills/",
            ".programisto/skills",
            "programisto/skills",
            "skills_catalog",
        ]

        skills_indexed = 0

        for location in skill_locations:
            skills_dir = os.path.join(repo_dir, location)
            if os.path.exists(skills_dir):
                skills_indexed += self._index_skills_directory(skills_dir)

        # Also check for JSON skill files
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                if file.endswith(".json"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r") as f:
                            import json
                            data = json.load(f)
                            if "skills" in data:
                                skills_indexed += len(data["skills"])
                    except (json.JSONDecodeError, IOError):
                        pass

        return skills_indexed

    def _index_skills_directory(self, skills_dir: str) -> int:
        """Index skills from a directory."""
        skills_count = 0

        for root, dirs, files in os.walk(skills_dir):
            for file in files:
                if file.endswith((".json", ".yaml", ".yml")):
                    skills_count += 1

        return skills_count

    def add_cli(self, cli_name: str) -> AdminResult:
        """Register a new CLI tool for configuration.

        Args:
            cli_name: Name of the CLI tool.

        Returns:
            AdminResult with status.
        """
        # Normalize name
        cli_name = cli_name.lower().strip()

        # Validate against supported tools
        supported = self.cli_support.DEFAULT_TOOLS.keys()
        matching = self._find_matching_tool(cli_name, supported)

        if not matching:
            return AdminResult(
                success=False,
                message=f"Unknown CLI tool: {cli_name}. "
                        f"Supported tools: {', '.join(supported)}",
            )

        # Add the tool
        self.cli_support.add_tool(cli_name)

        # Save configuration
        self.cli_support.save_config()

        # Generate installation instructions
        instructions = self._get_installation_instructions(matching)

        return AdminResult(
            success=True,
            message=f"Successfully registered CLI tool '{cli_name}'. "
                    f"Configuration saved to {self.cli_support.config_path}",
            data={
                "cli_name": cli_name,
                "matched_tool": matching,
                "instructions": instructions,
            },
        )

    def _find_matching_tool(
        self,
        name: str,
        supported: set,
    ) -> Optional[str]:
        """Find a matching tool from supported list."""
        name_lower = name.lower()

        for tool in supported:
            if tool in name_lower or name_lower in tool:
                return tool

        return None

    def _get_installation_instructions(self, tool: str) -> str:
        """Get installation instructions for a tool."""
        instructions = {
            "claude_code": """
To install Claude Code:
1. Visit https://claude.ai/code
2. Download and install the CLI
3. Follow the on-screen setup instructions
""",
            "codex": """
To install OpenAI Codex:
1. pip install codex-cli
2. Configure with 'codex login'
""",
            "cursor": """
To install Cursor:
1. Visit https://cursor.sh
2. Download and install the editor
3. Open your project to enable skills
""",
            "gemini": """
To install Gemini CLI:
1. npm install -g @google/gemini-cli
2. Run 'gemini login' to authenticate
""",
            "aider": """
To install Aider:
1. pip install aider-chat
2. Run 'aider' in your project directory
""",
        }

        return instructions.get(tool, f"""
To configure {tool}:
1. Ensure the tool is installed on your system
2. The configuration has been added to programisto-config.yaml
3. Follow the tool's documentation for skill integration
""")

    def new_project(
        self,
        project_name: str,
        template: Optional[str] = None,
    ) -> AdminResult:
        """Initialize a new project with Programisto.

        Args:
            project_name: Name of the new project.
            template: Optional template to use.

        Returns:
            AdminResult with status.
        """
        # Validate project name
        if not project_name or not project_name.strip():
            return AdminResult(
                success=False,
                message="Project name is required",
            )

        project_name = project_name.strip()

        # Create project directory
        project_dir = os.path.abspath(project_name)

        if os.path.exists(project_dir):
            return AdminResult(
                success=False,
                message=f"Directory already exists: {project_dir}",
            )

        try:
            # Create directory structure
            os.makedirs(project_dir, exist_ok=True)

            # Initialize programisto config
            config = ProgramistoConfig(
                project_dir=project_dir,
            )
            save_config(config, os.path.join(project_dir, "programisto-config.yaml"))

            # Set up project-specific skill catalog
            self._setup_skill_catalog(project_dir)

            # Generate initial project context
            self._generate_project_context(project_dir, template)

            return AdminResult(
                success=True,
                message=f"Successfully created new project '{project_name}'",
                data={
                    "project_dir": project_dir,
                    "template": template,
                },
            )

        except Exception as e:
            # Clean up on failure
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)

            return AdminResult(
                success=False,
                message=f"Failed to create project: {e}",
            )

    def _setup_skill_catalog(self, project_dir: str) -> None:
        """Set up project-specific skill catalog."""
        # Copy skills catalog
        catalog_dir = os.path.join(project_dir, "skills_catalog")
        os.makedirs(catalog_dir, exist_ok=True)

        # Create a minimal skills file
        skills_file = os.path.join(catalog_dir, "skills.json")
        with open(skills_file, "w") as f:
            import json
            json.dump({
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "skills": [],
            }, f, indent=2)

    def _generate_project_context(
        self,
        project_dir: str,
        template: Optional[str],
    ) -> None:
        """Generate initial project context file."""
        context_file = os.path.join(project_dir, "PROJECT_CONTEXT.md")

        context = f"""# {os.path.basename(project_dir)}

## Project Information

- **Created**: {datetime.now().isoformat()}
- **Programisto Version**: 1.0.0

## Project Structure

This project is managed by Programisto, your coding companion.

### Key Directories

- `src/` - Source code
- `tests/` - Test files
- `skills_catalog/` - Skill definitions
- `.programisto/` - Programisto data

### Getting Started

1. Run `programisto help` to see available commands
2. Run `programisto scan` to analyze your project
3. Use `programisto foil` to generate code patterns
4. Use `programisto harness` to generate engineering tools

## Configuration

Programisto configuration is stored in `programisto-config.yaml`.

## Skills

Skills are defined in `skills_catalog/skills.json`.

Add custom skills by adding entries to the skills catalog.
"""

        with open(context_file, "w") as f:
            f.write(context)

    def list_skills(self) -> AdminResult:
        """List all available skills.

        Returns:
            AdminResult with skill list.
        """
        self.catalog.ensure_index()

        skills = []
        if self.catalog.index:
            for skill_id, metadata in self.catalog.index.skills.items():
                skills.append({
                    "id": metadata.id,
                    "name": metadata.name,
                    "category": metadata.category,
                    "tags": metadata.tags,
                    "priority": metadata.priority,
                })

        return AdminResult(
            success=True,
            message=f"Found {len(skills)} skills",
            data={"skills": skills},
        )

    def list_tools(self) -> AdminResult:
        """List all configured CLI tools.

        Returns:
            AdminResult with tool list.
        """
        tools = []
        for tool_name in self.cli_support.DEFAULT_TOOLS:
            config = self.cli_support.get_tool_config(tool_name.replace("_", "-"))
            if config:
                tools.append({
                    "name": tool_name.replace("_", "-"),
                    "enabled": config.get("enabled", False),
                    "skills_dir": config.get("skills_dir"),
                    "activation": config.get("activation"),
                })

        return AdminResult(
            success=True,
            message=f"Found {len(tools)} tools",
            data={"tools": tools},
        )

    def validate_project(self, project_path: Optional[str] = None) -> AdminResult:
        """Validate a project's Programisto setup.

        Args:
            project_path: Path to validate. Defaults to current directory.

        Returns:
            AdminResult with validation status.
        """
        project_path = project_path or os.getcwd()

        issues = []
        warnings = []

        # Check for config file
        config_path = os.path.join(project_path, "programisto-config.yaml")
        if not os.path.exists(config_path):
            warnings.append("No programisto-config.yaml found")

        # Check for skills catalog
        skills_dir = os.path.join(project_path, "skills_catalog")
        if not os.path.exists(skills_dir):
            warnings.append("No skills_catalog directory found")

        # Check for context file
        context_file = os.path.join(project_path, "PROJECT_CONTEXT.md")
        if not os.path.exists(context_file):
            warnings.append("No PROJECT_CONTEXT.md found")

        # Validate CLI config
        cli_errors = self.cli_support.validate_config()
        if cli_errors:
            issues.extend(cli_errors)

        return AdminResult(
            success=len(issues) == 0,
            message=f"Validation complete. {len(issues)} issues, {len(warnings)} warnings",
            data={
                "issues": issues,
                "warnings": warnings,
                "project_path": project_path,
            },
        )


# Global admin instance
_admin: Optional[AdminCommands] = None


def get_admin(config: Optional[ProgramistoConfig] = None) -> AdminCommands:
    """Get or create the global admin instance.

    Args:
        config: Optional configuration.

    Returns:
        AdminCommands instance.
    """
    global _admin

    if _admin is None:
        _admin = AdminCommands(config)

    return _admin
