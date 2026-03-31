"""Sample skill data for testing."""

from typing import Dict, List, Any


# Sample skill catalog data
SAMPLE_SKILL_CATALOG = {
    "version": "1.0.0",
    "last_updated": "2026-03-31",
    "skills": [
        {
            "id": "web-components",
            "name": "Web Components",
            "description": "Reusable custom HTML elements",
            "category": "frontend",
            "tags": ["components", "web-components", "javascript"],
            "supported_agents": ["claude-code", "cursor", "aider"],
            "files": ["components/base-component.ts"],
            "priority": "high",
        },
        {
            "id": "react-hooks",
            "name": "React Custom Hooks",
            "description": "Reusable stateful logic",
            "category": "frontend",
            "tags": ["react", "hooks", "typescript"],
            "supported_agents": ["claude-code", "codex", "cursor"],
            "files": ["hooks/useAsync.ts"],
            "priority": "high",
        },
        {
            "id": "state-management",
            "name": "State Management",
            "description": "Centralized state management",
            "category": "frontend",
            "tags": ["state", "context", "typescript"],
            "supported_agents": ["claude-code", "cursor"],
            "files": ["store/context.tsx"],
            "priority": "high",
        },
        {
            "id": "api-client",
            "name": "API Client",
            "description": "Type-safe API client",
            "category": "frontend",
            "tags": ["api", "axios", "typescript"],
            "supported_agents": ["claude-code", "codex", "aider"],
            "files": ["api/client.ts"],
            "priority": "medium",
        },
        {
            "id": "validation",
            "name": "Form Validation",
            "description": "Type-safe validation",
            "category": "frontend",
            "tags": ["validation", "forms", "zod"],
            "supported_agents": ["claude-code", "cursor"],
            "files": ["validation/schema.ts"],
            "priority": "medium",
        },
        {
            "id": "testing",
            "name": "Testing Setup",
            "description": "Jest/RTL testing",
            "category": "testing",
            "tags": ["testing", "jest", "react-testing-library"],
            "supported_agents": ["claude-code", "codex", "cursor", "aider"],
            "files": ["tests/setup.ts"],
            "priority": "medium",
        },
    ],
}


def get_sample_skill(id: str) -> Dict[str, Any]:
    """Get a sample skill by ID."""
    for skill in SAMPLE_SKILL_CATALOG["skills"]:
        if skill["id"] == id:
            return skill
    return {}


def get_sample_skills_by_category(category: str) -> List[Dict[str, Any]]:
    """Get sample skills by category."""
    return [
        s for s in SAMPLE_SKILL_CATALOG["skills"]
        if s["category"] == category
    ]


def get_sample_skills_by_tag(tag: str) -> List[Dict[str, Any]]:
    """Get sample skills by tag."""
    return [
        s for s in SAMPLE_SKILL_CATALOG["skills"]
        if tag in s["tags"]
    ]


def get_sample_skills_by_agent(agent: str) -> List[Dict[str, Any]]:
    """Get sample skills by supported agent."""
    return [
        s for s in SAMPLE_SKILL_CATALOG["skills"]
        if agent in s["supported_agents"]
    ]


# Sample skill metadata for testing
SAMPLE_SKILL_METADATA = {
    "id": "web-components",
    "name": "Web Components",
    "description": "Reusable custom HTML elements with Shadow DOM",
    "category": "frontend",
    "tags": ["components", "web-components", "javascript", "typescript"],
    "supported_agents": ["claude-code", "cursor", "aider"],
    "priority": "high",
    "file_count": 3,
}
