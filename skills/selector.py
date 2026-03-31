"""Skill selector for Programisto.

Requirements 10, 11, 12, 13: Skill Selection and Application

Provides LLM-based skill selection, parameter generation with user confirmation,
and full skill set generation.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from scanner.project_scanner import ProjectStructure
from llm.client import LLMClient, ChatMessage, ChatRole
from skills.catalog import SkillCatalog, SkillMetadata, get_catalog


@dataclass
class SkillParameters:
    """Parameters for a skill."""

    skill_id: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "enabled": self.enabled,
            "config": self.config,
            "custom_settings": self.custom_settings,
            "order": self.order,
        }


@dataclass
class SkillSelection:
    """A skill selection result."""

    skill_id: str
    name: str
    description: str
    priority: str  # high, medium, low
    confidence: float  # 0-1
    justification: str
    parameters: List[SkillParameters] = field(default_factory=list)
    files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "confidence": self.confidence,
            "justification": self.justification,
            "parameters": [p.to_dict() for p in self.parameters],
            "files": self.files,
        }


@dataclass
class SkillSelectionResult:
    """Result of skill selection."""

    selected_skills: List[SkillSelection] = field(default_factory=list)
    excluded_skills: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_skills": [s.to_dict() for s in self.selected_skills],
            "excluded_skills": self.excluded_skills,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at,
        }


class SkillSelector:
    """Selects and configures skills based on project context."""

    def __init__(
        self,
        project_structure: Optional[ProjectStructure] = None,
        llm_client: Optional[LLMClient] = None,
        catalog: Optional[SkillCatalog] = None,
    ):
        """Initialize the skill selector.

        Args:
            project_structure: Project structure for context.
            llm_client: LLM client for recommendations.
            catalog: Skill catalog to use.
        """
        self.project_structure = project_structure
        self.llm_client = llm_client
        self.catalog = catalog or get_catalog()
        self.selections: Dict[str, SkillSelection] = {}

    def select_skills(
        self,
        project_structure: Optional[ProjectStructure] = None,
        use_llm: bool = True,
    ) -> SkillSelectionResult:
        """Select skills based on project context.

        Args:
            project_structure: Project structure to analyze.
            use_llm: Whether to use LLM for recommendations.

        Returns:
            SkillSelectionResult with selected skills.
        """
        if project_structure:
            self.project_structure = project_structure

        result = SkillSelectionResult()

        # Get all available skills
        all_skills = self.catalog.raw_skills.get("skills", [])

        if not all_skills:
            return result

        # Select skills based on context
        if use_llm and self.llm_client:
            # Use LLM for intelligent selection
            result = self._select_with_llm(all_skills)
        else:
            # Use rule-based selection
            result = self._select_rule_based(all_skills)

        return result

    def _select_rule_based(
        self,
        all_skills: List[Dict[str, Any]],
    ) -> SkillSelectionResult:
        """Select skills using rule-based logic.

        Args:
            all_skills: List of all available skills.

        Returns:
            SkillSelectionResult.
        """
        result = SkillSelectionResult()

        if not self.project_structure:
            # Return high-priority generic skills
            for skill in all_skills:
                if skill.get("priority") == "high":
                    selection = SkillSelection(
                        skill_id=skill.get("id", ""),
                        name=skill.get("name", ""),
                        description=skill.get("description", ""),
                        priority=skill.get("priority", "medium"),
                        confidence=0.9,
                        justification="High priority skill for all projects",
                        files=skill.get("files", []),
                    )
                    result.selected_skills.append(selection)
                    self.selections[selection.skill_id] = selection
            return result

        # Get technology stack
        tech_stack = self.project_structure.technology_stack

        for skill in all_skills:
            skill_id = skill.get("id", "")
            tags = skill.get("tags", [])
            priority = skill.get("priority", "medium")
            files = skill.get("files", [])

            # Calculate match score
            score = 0
            justifications = []

            # Check for TypeScript
            if tech_stack.get("typescript") or any("typescript" in t for t in tags):
                score += 2
                justifications.append("Project uses TypeScript")

            # Check for React
            if tech_stack.get("react") or any("react" in t for t in tags):
                score += 2
                justifications.append("Project uses React")

            # Check for specific tags
            if any("state" in t for t in tags):
                score += 1
                justifications.append("State management recommended")

            if any("api" in t for t in tags):
                score += 1
                justifications.append("API client recommended")

            # Determine if skill should be included
            if score >= 2 or priority == "high":
                selection = SkillSelection(
                    skill_id=skill_id,
                    name=skill.get("name", ""),
                    description=skill.get("description", ""),
                    priority=priority,
                    confidence=min(0.95, 0.5 + score * 0.2),
                    justification="; ".join(justifications) if justifications else "Recommended for project",
                    files=files,
                )
                result.selected_skills.append(selection)
                self.selections[skill_id] = selection
            else:
                result.excluded_skills.append(skill_id)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _select_with_llm(
        self,
        all_skills: List[Dict[str, Any]],
    ) -> SkillSelectionResult:
        """Select skills using LLM analysis.

        Args:
            all_skills: List of all available skills.

        Returns:
            SkillSelectionResult.
        """
        result = SkillSelectionResult()

        if not self.project_structure:
            return self._select_rule_based(all_skills)

        # Build context for LLM
        context = self._build_llm_context()

        # Build skill descriptions for LLM
        skill_descriptions = ""
        for skill in all_skills:
            skill_descriptions += f"""
- {skill.get('id', 'unknown')}: {skill.get('name', '')}
  Description: {skill.get('description', '')}
  Tags: {', '.join(skill.get('tags', []))}
  Priority: {skill.get('priority', 'medium')}
"""

        # Create prompt for LLM
        prompt = f"""Analyze this project and recommend the most relevant skills from the list below.

Project Context:
{context}

Available Skills:
{skill_descriptions}

For each skill, provide:
1. Whether it should be selected (yes/no)
2. Priority level (high/medium/low)
3. Confidence score (0-1)
4. Justification for the recommendation

Respond in JSON format with this structure:
{{
  "selected_skills": [
    {{
      "skill_id": "skill-id",
      "name": "Skill Name",
      "description": "Description",
      "priority": "high",
      "confidence": 0.9,
      "justification": "Why this skill is recommended",
      "files": ["file1", "file2"]
    }}
  ],
  "recommendations": ["Additional recommendations"]
}}"""

        # Call LLM
        try:
            messages = [
                ChatMessage(
                    ChatRole.SYSTEM,
                    "You are a skill selection assistant. Analyze projects and recommend the most relevant skills.",
                ),
                ChatMessage(ChatRole.USER, prompt),
            ]

            response = self.llm_client.chat(messages)
            selection = self._parse_llm_response(response.content)
            result = selection

        except Exception as e:
            # Fall back to rule-based selection
            print(f"LLM selection failed, falling back to rule-based: {e}")
            result = self._select_rule_based(all_skills)

        return result

    def _build_llm_context(self) -> str:
        """Build context for LLM analysis."""
        if not self.project_structure:
            return "No project context available"

        parts = [
            "## Project Structure",
            f"Root: {self.project_structure.root_path}",
            f"Files: {self.project_structure.file_count}",
            "",
            "## Technology Stack",
        ]

        for tech, enabled in self.project_structure.technology_stack.items():
            if enabled:
                parts.append(f"- {tech}")

        # Add key files
        parts.extend(["", "## Key Files"])
        for f in self.project_structure.config_files[:5]:
            parts.append(f"- {f.path}")

        return "\n".join(parts)

    def _parse_llm_response(self, response: str) -> SkillSelectionResult:
        """Parse LLM response into SkillSelectionResult."""
        # Try to extract JSON
        try:
            # Find JSON block
            import re
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group())

                result = SkillSelectionResult()

                for skill_data in data.get("selected_skills", []):
                    selection = SkillSelection(
                        skill_id=skill_data.get("skill_id", ""),
                        name=skill_data.get("name", ""),
                        description=skill_data.get("description", ""),
                        priority=skill_data.get("priority", "medium"),
                        confidence=skill_data.get("confidence", 0.5),
                        justification=skill_data.get("justification", ""),
                        files=skill_data.get("files", []),
                    )
                    result.selected_skills.append(selection)
                    self.selections[selection.skill_id] = selection

                result.recommendations = data.get("recommendations", [])

                return result

        except (json.JSONDecodeError, KeyError):
            pass

        # Fallback: create a basic result
        return SkillSelectionResult()

    def generate_parameters(
        self,
        selections: Optional[SkillSelectionResult] = None,
    ) -> Dict[str, SkillParameters]:
        """Generate parameters for selected skills.

        Args:
            selections: Optional skill selections. If not provided, uses
                       previously selected skills.

        Returns:
            Dictionary mapping skill IDs to parameters.
        """
        params: Dict[str, SkillParameters] = {}

        selections = selections or SkillSelectionResult(
            selected_skills=list(self.selections.values())
        )

        for selection in selections.selected_skills:
            skill_params = self._generate_skill_parameters(
                selection.skill_id, selection
            )
            params[selection.skill_id] = skill_params

        return params

    def _generate_skill_parameters(
        self,
        skill_id: str,
        selection: SkillSelection,
    ) -> SkillParameters:
        """Generate parameters for a specific skill."""
        # Get skill from catalog
        skill = self.catalog.get_skill(skill_id)

        # Default parameters
        params = SkillParameters(
            skill_id=skill_id,
            enabled=True,
            config={},
            custom_settings={},
            order=len(self.selections) + 1,
        )

        # Add skill-specific defaults
        if "typescript" in skill.tags if skill else False:
            params.config["strict"] = True
            params.config["module"] = "ESNext"

        if "react" in skill.tags if skill else False:
            params.config["hooks"] = True
            params.config["functional"] = True

        return params

    def present_for_confirmation(
        self,
        selections: Optional[SkillSelectionResult] = None,
    ) -> str:
        """Present selected skills for user confirmation.

        Args:
            selections: Optional skill selections.

        Returns:
            Formatted string for display.
        """
        selections = selections or self.select_skills()

        lines = [
            "## Skill Selection",
            "",
            f"Generated: {selections.generated_at}",
            "",
            f"Selected Skills: {len(selections.selected_skills)}",
            "",
        ]

        for selection in sorted(
            selections.selected_skills,
            key=lambda s: {"high": 0, "medium": 1, "low": 2}.get(s.priority, 3),
        ):
            lines.extend([
                f"### {selection.name} ({selection.skill_id})",
                f"Description: {selection.description}",
                f"Priority: {selection.priority}",
                f"Confidence: {selection.confidence:.0%}",
                f"Justification: {selection.justification}",
                "",
            ])

        if selections.recommendations:
            lines.extend([
                "## Recommendations",
                *["- " + rec for rec in selections.recommendations],
                "",
            ])

        lines.append(
            "Reply with:\n"
            "- 'accept' to accept all selections\n"
            "- 'reject' to reject all selections\n"
            "- 'modify <skill_id>' to modify a specific skill\n"
            "- 'exclude <skill_id>' to exclude a skill\n"
            "- Any other feedback to regenerate with new context"
        )

        return "\n".join(lines)

    def process_user_feedback(
        self,
        feedback: str,
        selections: Optional[SkillSelectionResult] = None,
    ) -> Optional[SkillSelectionResult]:
        """Process user feedback on skill selections.

        Args:
            feedback: User's feedback string.
            selections: Original selections to modify.

        Returns:
            Modified selections, or None if feedback is invalid.
        """
        selections = selections or self.select_skills()

        feedback_lower = feedback.lower().strip()

        # Handle accept
        if feedback_lower == "accept":
            return selections

        # Handle reject
        if feedback_lower == "reject":
            return SkillSelectionResult()

        # Handle modify
        if feedback_lower.startswith("modify "):
            skill_id = feedback_lower[7:].strip()
            return self._modify_skill(skill_id, selections)

        # Handle exclude
        if feedback_lower.startswith("exclude "):
            skill_id = feedback_lower[8:].strip()
            return self._exclude_skill(skill_id, selections)

        # Otherwise, use feedback as new context and regenerate
        return self.select_skills(use_llm=True)

    def _modify_skill(
        self,
        skill_id: str,
        selections: SkillSelectionResult,
    ) -> SkillSelectionResult:
        """Modify a specific skill selection."""
        for selection in selections.selected_skills:
            if selection.skill_id == skill_id:
                # Prompt for modification details
                print(f"Modifying skill: {selection.name}")
                print(f"Current justification: {selection.justification}")
                print("Enter new justification (or press Enter to keep current):")
                new_justification = input().strip()
                if new_justification:
                    selection.justification = new_justification
                break

        return selections

    def _exclude_skill(
        self,
        skill_id: str,
        selections: SkillSelectionResult,
    ) -> SkillSelectionResult:
        """Exclude a specific skill."""
        selected = [
            s for s in selections.selected_skills
            if s.skill_id != skill_id
        ]
        if skill_id not in selections.excluded_skills:
            selections.excluded_skills.append(skill_id)

        return SkillSelectionResult(
            selected_skills=selected,
            excluded_skills=selections.excluded_skills,
            recommendations=selections.recommendations,
        )

    def generate_full_skill_set(
        self,
        selections: SkillSelectionResult,
        params: Optional[Dict[str, SkillParameters]] = None,
    ) -> Dict[str, Any]:
        """Generate the full skill set after confirmation.

        Args:
            selections: Confirmed skill selections.
            params: Optional parameters for each skill.

        Returns:
            Complete skill set configuration.
        """
        params = params or self.generate_parameters(selections)

        # Build full skill set
        skill_set = {
            "generated_at": datetime.now().isoformat(),
            "skills": [],
            "configuration": {},
            "files": [],
        }

        for selection in selections.selected_skills:
            skill_config = {
                "id": selection.skill_id,
                "name": selection.name,
                "enabled": True,
                "priority": selection.priority,
                "parameters": params.get(selection.skill_id, SkillParameters(
                    skill_id=selection.skill_id
                )).to_dict(),
                "files": selection.files,
            }
            skill_set["skills"].append(skill_config)

            # Collect files
            skill_set["files"].extend(selection.files)

        skill_set["configuration"] = self._build_configuration(selections)

        return skill_set

    def _build_configuration(
        self,
        selections: SkillSelectionResult,
    ) -> Dict[str, Any]:
        """Build configuration from selections."""
        config = {
            "version": "1.0.0",
            "skills_enabled": len(selections.selected_skills),
            "settings": {},
        }

        # Add skill-specific settings
        for selection in selections.selected_skills:
            config["settings"][selection.skill_id] = {
                "enabled": True,
                "priority": selection.priority,
            }

        return config

    def provide_integration_guidance(
        self,
        skill_id: str,
        project_structure: Optional[ProjectStructure] = None,
    ) -> str:
        """Provide step-by-step guidance for integrating a skill.

        Args:
            skill_id: The skill to provide guidance for.
            project_structure: Optional project structure.

        Returns:
            Integration guidance string.
        """
        skill = self.catalog.get_skill(skill_id)

        if not skill:
            return f"Skill '{skill_id}' not found in catalog."

        lines = [
            f"## Integration Guide: {skill.name}",
            "",
            f"Description: {skill.description}",
            "",
            "### Step 1: Install Dependencies",
        ]

        # Add installation steps based on skill
        if "typescript" in skill.tags:
            lines.extend([
                "```bash",
                "npm install typescript @types/node --save-dev",
                "```",
                "",
            ])

        if "react" in skill.tags:
            lines.extend([
                "```bash",
                "npm install react react-dom --save",
                "```",
                "",
            ])

        lines.extend([
            "### Step 2: Create Configuration Files",
            "",
            "Based on the skill requirements, create the necessary configuration files",
            "in your project directory.",
            "",
            "### Step 3: Implement the Skill",
            "",
            "Follow the patterns and templates provided in the skill files.",
            "",
            "### Step 4: Test Integration",
            "",
            "Run tests to ensure the skill integrates correctly with your project.",
            "",
            "### Step 5: Documentation",
            "",
            "Update your project documentation to reflect the new skill.",
        ])

        return "\n".join(lines)


# Global selector instance
_selector: Optional[SkillSelector] = None


def get_selector(
    project_structure: Optional[ProjectStructure] = None,
) -> SkillSelector:
    """Get or create the global skill selector."""
    global _selector

    if _selector is None:
        _selector = SkillSelector(project_structure)

    return _selector
