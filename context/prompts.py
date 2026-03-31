"""Context-aware prompt construction for Programisto.

Requirement 9: Context-Aware Prompts

Constructs prompts that include TypeScript context, business direction,
project goals, and project documentation. Limited to current project scope.
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from scanner.project_scanner import ProjectStructure, FileAnalysis


@dataclass
class ContextData:
    """Context data for prompt construction."""

    project_name: str = "unknown"
    technology_stack: Dict[str, bool] = field(default_factory=dict)
    project_files: List[str] = field(default_factory=list)
    key_files: Dict[str, str] = field(default_factory=dict)
    documentation: Dict[str, str] = field(default_factory=dict)
    business_direction: str = ""
    project_goals: List[str] = field(default_factory=list)
    recent_changes: List[str] = field(default_factory=list)
    log_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "technology_stack": self.technology_stack,
            "project_files": self.project_files,
            "key_files": self.key_files,
            "documentation": self.documentation,
            "business_direction": self.business_direction,
            "project_goals": self.project_goals,
            "recent_changes": self.recent_changes,
            "log_summary": self.log_summary,
        }


class ContextPromptBuilder:
    """Builds context-aware prompts for LLM queries."""

    # Key files that provide important context
    KEY_FILES = {
        "package.json": "dependencies",
        "tsconfig.json": "typescript-config",
        "pyproject.toml": "python-config",
        "requirements.txt": "python-deps",
        "README.md": "project-documentation",
        "Dockerfile": "docker-config",
        ".env.example": "environment-config",
        "src/main.tsx": "entry-point",
        "src/App.tsx": "main-component",
        "src/index.css": "global-styles",
    }

    # Documentation file patterns
    DOC_PATTERNS = {
        "*.md",
        "*.mdx",
        "docs/**/*",
        "documentation/**/*",
    }

    def __init__(self, project_structure: Optional[ProjectStructure] = None):
        """Initialize the prompt builder.

        Args:
            project_structure: Optional pre-scanned project structure.
        """
        self.project_structure = project_structure
        self.context_data = ContextData()

    def build_context(self, project_structure: Optional[ProjectStructure] = None) -> ContextData:
        """Build context data from a project structure.

        Args:
            project_structure: The project to build context for.

        Returns:
            ContextData with extracted context.
        """
        if project_structure:
            self.project_structure = project_structure

        if not self.project_structure:
            return self.context_data

        # Extract project name
        self.context_data.project_name = os.path.basename(
            self.project_structure.root_path
        ) or "unknown"

        # Extract technology stack
        self.context_data.technology_stack = (
            self.project_structure.technology_stack
        )

        # Build file lists
        all_files = (
            self.project_structure.source_files
            + self.project_structure.config_files
        )
        self.context_data.project_files = [f.path for f in all_files]

        # Identify key files
        self._identify_key_files()

        # Extract documentation
        self._extract_documentation()

        return self.context_data

    def _identify_key_files(self) -> None:
        """Identify key files and their purpose."""
        all_files = [f.path for f in self.project_structure.source_files]
        all_files.extend([f.path for f in self.project_structure.config_files])

        for filepath, purpose in self.KEY_FILES.items():
            for file in all_files:
                if self._match_pattern(file, filepath):
                    self.context_data.key_files[purpose] = file
                    break

    def _extract_documentation(self) -> None:
        """Extract documentation content."""
        doc_content: Dict[str, str] = {}

        # Look for README and other docs
        readme_patterns = ["README.md", "readme.md", "README.MD"]
        for pattern in readme_patterns:
            if pattern in self.context_data.project_files:
                doc_content["README"] = pattern
                break

        # Check for docs directory
        for file in self.context_data.project_files:
            if "docs" in file and file.endswith(".md"):
                doc_content[file] = file

        self.context_data.documentation = doc_content

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Simple glob pattern matching."""
        import fnmatch

        basename = os.path.basename(path)
        return fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(
            path, pattern
        )

    def build_prompt(
        self,
        user_query: str,
        context_data: Optional[ContextData] = None,
        include_file_content: bool = True,
        max_file_content: int = 5,
    ) -> str:
        """Build a context-aware prompt.

        Args:
            user_query: The user's query or request.
            context_data: Optional context data. If not provided, builds from
                         current project structure.
            include_file_content: Whether to include actual file contents.
            max_file_content: Maximum number of files to include content for.

        Returns:
            The complete prompt string.
        """
        if context_data is None:
            context_data = self.build_context()

        parts = []

        # Project context header
        parts.append(self._build_project_context(context_data))

        # Technology stack
        tech_stack = self._build_technology_context(context_data)
        if tech_stack:
            parts.append(tech_stack)

        # Key file contents
        if include_file_content:
            file_context = self._build_file_context(
                context_data, max_file_content
            )
            if file_context:
                parts.append(file_context)

        # Documentation context
        if context_data.documentation:
            doc_context = self._build_documentation_context(context_data)
            if doc_context:
                parts.append(doc_context)

        # Business direction and goals
        if context_data.business_direction or context_data.project_goals:
            parts.append(self._build_business_context(context_data))

        # Log summary
        if context_data.log_summary:
            parts.append(f"## Log Summary\n\n{context_data.log_summary}")

        # User query with context
        parts.append(f"## User Query\n\n{user_query}")

        return "\n\n".join(parts)

    def _build_project_context(self, context: ContextData) -> str:
        """Build the project context section."""
        lines = [
            "## Project Context",
            f"- **Project Name**: {context.project_name}",
            f"- **Scan Date**: {datetime.now().isoformat()}",
            "",
        ]

        return "\n".join(lines)

    def _build_technology_context(self, context: ContextData) -> str:
        """Build the technology stack context."""
        if not context.technology_stack:
            return ""

        tech_list = [
            tech.capitalize()
            for tech, enabled in context.technology_stack.items()
            if enabled
        ]

        lines = [
            "## Technology Stack",
            f"Detected: {', '.join(tech_list)}",
            "",
        ]

        # Add TypeScript-specific context
        if context.technology_stack.get("typescript"):
            lines.extend(
                [
                    "### TypeScript Context",
                    "- Strongly typed codebase",
                    "- Use strict type annotations",
                    "- Prefer interfaces for public APIs",
                    "- Use type inference where appropriate",
                    "",
                ]
            )

        return "\n".join(lines)

    def _build_file_context(
        self, context: ContextData, max_files: int
    ) -> str:
        """Build the file context section with actual content."""
        if not context.key_files:
            return ""

        lines = ["## Key Files", ""]

        file_contents = []
        for purpose, filepath in list(context.key_files.items())[:max_files]:
            content = self._read_file_content(filepath)
            if content:
                file_contents.append((purpose, filepath, content))

        for purpose, filepath, content in file_contents:
            lines.extend(
                [
                    f"### {purpose} ({filepath})",
                    "```",
                    content,
                    "```",
                    "",
                ]
            )

        return "\n".join(lines)

    def _read_file_content(self, filepath: str) -> str:
        """Read file content, limited to first 200 lines."""
        try:
            full_path = os.path.join(
                self.project_structure.root_path if self.project_structure else ".",
                filepath,
            )

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[:200]

            content = "".join(lines)

            if len(lines) >= 200:
                content += "\n... (truncated)"

            return content

        except Exception:
            return "# Could not read file"

    def _build_documentation_context(self, context: ContextData) -> str:
        """Build the documentation context section."""
        lines = ["## Project Documentation", ""]

        for doc_name, filepath in context.documentation.items():
            content = self._read_file_content(filepath)
            lines.extend(
                [
                    f"### {doc_name}",
                    f"File: {filepath}",
                    "```",
                    content,
                    "```",
                    "",
                ]
            )

        return "\n".join(lines)

    def _build_business_context(self, context: ContextData) -> str:
        """Build the business direction and goals section."""
        lines = ["## Business Context", ""]

        if context.business_direction:
            lines.extend(
                [
                    "### Business Direction",
                    context.business_direction,
                    "",
                ]
            )

        if context.project_goals:
            lines.extend(
                [
                    "### Project Goals",
                    *["- " + goal for goal in context.project_goals],
                    "",
                ]
            )

        return "\n".join(lines)

    def add_context_info(
        self,
        project_name: Optional[str] = None,
        business_direction: Optional[str] = None,
        project_goals: Optional[List[str]] = None,
    ) -> None:
        """Manually add context information.

        Args:
            project_name: Name of the project.
            business_direction: Business direction or description.
            project_goals: List of project goals.
        """
        if project_name:
            self.context_data.project_name = project_name

        if business_direction:
            self.context_data.business_direction = business_direction

        if project_goals:
            self.context_data.project_goals = project_goals
