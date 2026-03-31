"""Skill catalog for Programisto.

Requirement 14: Skill Catalog Indexing

Indexes external skill catalogs for faster access. Creates an index of
available skills with metadata (names, descriptions, categories, tags,
supported agents).
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class SkillMetadata:
    """Metadata for a single skill."""

    id: str
    name: str
    description: str
    category: str
    tags: List[str] = field(default_factory=list)
    supported_agents: List[str] = field(default_factory=list)
    priority: str = "medium"
    file_count: int = 0
    last_indexed: Optional[str] = None
    content_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkillIndex:
    """Complete skill index."""

    version: str = "1.0.0"
    last_updated: Optional[str] = None
    skills: Dict[str, SkillMetadata] = field(default_factory=dict)
    categories: Dict[str, List[str]] = field(default_factory=dict)
    tags: Dict[str, List[str]] = field(default_factory=dict)
    total_skills: int = 0
    index_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "last_updated": self.last_updated,
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
            "categories": self.categories,
            "tags": self.tags,
            "total_skills": self.total_skills,
            "index_hash": self.index_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillIndex":
        """Create SkillIndex from dictionary."""
        index = cls()
        index.version = data.get("version", "1.0.0")
        index.last_updated = data.get("last_updated")
        index.index_hash = data.get("index_hash", "")
        index.total_skills = data.get("total_skills", 0)

        # Reconstruct skills
        for skill_id, skill_data in data.get("skills", {}).items():
            index.skills[skill_id] = SkillMetadata(
                id=skill_data.get("id", skill_id),
                name=skill_data.get("name", ""),
                description=skill_data.get("description", ""),
                category=skill_data.get("category", "general"),
                tags=skill_data.get("tags", []),
                supported_agents=skill_data.get("supported_agents", []),
                priority=skill_data.get("priority", "medium"),
                file_count=skill_data.get("file_count", 0),
                last_indexed=skill_data.get("last_indexed"),
                content_hash=skill_data.get("content_hash", ""),
            )

        # Reconstruct categories
        index.categories = data.get("categories", {})

        # Reconstruct tags
        index.tags = data.get("tags", {})

        return index


class SkillCatalog:
    """Skill catalog management."""

    INDEX_TTL = timedelta(hours=24)  # Index refresh every 24 hours

    def __init__(
        self,
        catalog_path: str = "skills_catalog/skills.json",
        index_path: str = "skills_catalog/skills_index.json",
    ):
        """Initialize the skill catalog.

        Args:
            catalog_path: Path to the skills JSON file.
            index_path: Path to store the skill index.
        """
        self.catalog_path = catalog_path
        self.index_path = index_path
        self.index: Optional[SkillIndex] = None
        self.raw_skills: Dict[str, Any] = {}

    def load_catalog(self) -> Dict[str, Any]:
        """Load the raw skill catalog.

        Returns:
            Dictionary of raw skill data.
        """
        if not os.path.exists(self.catalog_path):
            return {}

        with open(self.catalog_path, "r") as f:
            self.raw_skills = json.load(f)

        return self.raw_skills

    def index_skills(self) -> SkillIndex:
        """Index all skills in the catalog.

        Returns:
            SkillIndex with indexed skills.
        """
        # Load catalog if not loaded
        if not self.raw_skills:
            self.load_catalog()

        # Create new index
        index = SkillIndex()
        index.version = self.raw_skills.get("version", "1.0.0")
        index.last_updated = datetime.now().isoformat()

        # Track categories and tags
        categories: Dict[str, List[str]] = {}
        tags: Dict[str, List[str]] = {}

        # Index each skill
        for skill in self.raw_skills.get("skills", []):
            skill_id = skill.get("id")
            if not skill_id:
                continue

            # Calculate content hash
            content_hash = self._calculate_skill_hash(skill)

            # Create metadata
            metadata = SkillMetadata(
                id=skill_id,
                name=skill.get("name", skill_id),
                description=skill.get("description", ""),
                category=skill.get("category", "general"),
                tags=skill.get("tags", []),
                supported_agents=skill.get("supported_agents", []),
                priority=skill.get("priority", "medium"),
                file_count=len(skill.get("files", [])),
                last_indexed=index.last_updated,
                content_hash=content_hash,
            )

            index.skills[skill_id] = metadata
            index.total_skills += 1

            # Track categories
            category = metadata.category
            if category not in categories:
                categories[category] = []
            categories[category].append(skill_id)

            # Track tags
            for tag in metadata.tags:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(skill_id)

        index.categories = categories
        index.tags = tags

        # Calculate index hash
        index.index_hash = self._calculate_index_hash(index)

        self.index = index
        self._save_index()

        return index

    def _calculate_skill_hash(self, skill: Dict[str, Any]) -> str:
        """Calculate a hash for a skill's content."""
        # Hash based on key attributes
        content = json.dumps(
            {
                "id": skill.get("id"),
                "name": skill.get("name"),
                "description": skill.get("description"),
                "category": skill.get("category"),
                "tags": skill.get("tags", []),
                "files": skill.get("files", []),
            },
            sort_keys=True,
        )
        return hashlib.md5(content.encode()).hexdigest()

    def _calculate_index_hash(self, index: SkillIndex) -> str:
        """Calculate a hash for the entire index."""
        # Hash based on version and skill hashes
        skill_hashes = [
            skill.content_hash
            for skill in index.skills.values()
        ]
        content = json.dumps(
            {
                "version": index.version,
                "skill_hashes": sorted(skill_hashes),
            },
            sort_keys=True,
        )
        return hashlib.md5(content.encode()).hexdigest()

    def _save_index(self) -> None:
        """Save the index to disk."""
        if self.index:
            index_dir = os.path.dirname(self.index_path)
            if index_dir:
                os.makedirs(index_dir, exist_ok=True)

            with open(self.index_path, "w") as f:
                json.dump(self.index.to_dict(), f, indent=2)

    def load_index(self) -> Optional[SkillIndex]:
        """Load the index from disk if valid.

        Returns:
            SkillIndex if valid, None otherwise.
        """
        if not os.path.exists(self.index_path):
            return None

        try:
            with open(self.index_path, "r") as f:
                data = json.load(f)

            index = SkillIndex.from_dict(data)

            # Check if index is still valid
            if index.last_updated:
                last_updated = datetime.fromisoformat(index.last_updated)
                if datetime.now() - last_updated > self.INDEX_TTL:
                    # Index has expired
                    return None

            # Check if source catalog has changed
            if self._catalog_changed(index):
                return None

            self.index = index
            return index

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Failed to load index: {e}")
            return None

    def _catalog_changed(self, index: SkillIndex) -> bool:
        """Check if the source catalog has changed since indexing.

        Args:
            index: The existing index to check against.

        Returns:
            True if catalog has changed, False otherwise.
        """
        if not os.path.exists(self.catalog_path):
            return True

        try:
            with open(self.catalog_path, "r") as f:
                current_data = json.load(f)

            # Check version
            if current_data.get("version") != index.version:
                return True

            # Check skill hashes
            current_skills = {s.get("id"): s for s in current_data.get("skills", [])}
            for skill_id, stored_skill in index.skills.items():
                if skill_id not in current_skills:
                    return True
                current_hash = self._calculate_skill_hash(current_skills[skill_id])
                if current_hash != stored_skill.content_hash:
                    return True

            return False

        except (json.JSONDecodeError, KeyError):
            return True

    def ensure_index(self) -> SkillIndex:
        """Ensure an index exists, creating it if necessary.

        Returns:
            SkillIndex.
        """
        # Try to load existing index
        index = self.load_index()
        if index:
            return index

        # Create new index
        return self.index_skills()

    def get_skill(self, skill_id: str) -> Optional[SkillMetadata]:
        """Get a skill by ID.

        Args:
            skill_id: The skill ID.

        Returns:
            SkillMetadata if found, None otherwise.
        """
        if not self.index:
            self.ensure_index()

        if self.index and skill_id in self.index.skills:
            return self.index.skills[skill_id]

        # Search in raw skills
        for skill in self.raw_skills.get("skills", []):
            if skill.get("id") == skill_id:
                # Create metadata on the fly
                return SkillMetadata(
                    id=skill.get("id", skill_id),
                    name=skill.get("name", skill_id),
                    description=skill.get("description", ""),
                    category=skill.get("category", "general"),
                    tags=skill.get("tags", []),
                    supported_agents=skill.get("supported_agents", []),
                    priority=skill.get("priority", "medium"),
                    file_count=len(skill.get("files", [])),
                )

        return None

    def get_skills_by_category(self, category: str) -> List[SkillMetadata]:
        """Get all skills in a category.

        Args:
            category: The category name.

        Returns:
            List of SkillMetadata.
        """
        if not self.index:
            self.ensure_index()

        if self.index and category in self.index.categories:
            return [
                self.index.skills[skill_id]
                for skill_id in self.index.categories[category]
                if skill_id in self.index.skills
            ]

        # Search in raw skills
        return [
            SkillMetadata(
                id=skill.get("id", ""),
                name=skill.get("name", ""),
                description=skill.get("description", ""),
                category=skill.get("category", "general"),
                tags=skill.get("tags", []),
                supported_agents=skill.get("supported_agents", []),
                priority=skill.get("priority", "medium"),
                file_count=len(skill.get("files", [])),
            )
            for skill in self.raw_skills.get("skills", [])
            if skill.get("category") == category
        ]

    def get_skills_by_tag(self, tag: str) -> List[SkillMetadata]:
        """Get all skills with a specific tag.

        Args:
            tag: The tag name.

        Returns:
            List of SkillMetadata.
        """
        if not self.index:
            self.ensure_index()

        if self.index and tag in self.index.tags:
            return [
                self.index.skills[skill_id]
                for skill_id in self.index.tags[tag]
                if skill_id in self.index.skills
            ]

        # Search in raw skills
        return [
            SkillMetadata(
                id=skill.get("id", ""),
                name=skill.get("name", ""),
                description=skill.get("description", ""),
                category=skill.get("category", "general"),
                tags=skill.get("tags", []),
                supported_agents=skill.get("supported_agents", []),
                priority=skill.get("priority", "medium"),
                file_count=len(skill.get("files", [])),
            )
            for skill in self.raw_skills.get("skills", [])
            if tag in skill.get("tags", [])
        ]

    def get_skills_by_agent(self, agent: str) -> List[SkillMetadata]:
        """Get all skills supported by a specific agent.

        Args:
            agent: The agent name (e.g., "claude-code", "cursor").

        Returns:
            List of SkillMetadata.
        """
        if not self.index:
            self.ensure_index()

        if self.index:
            return [
                skill
                for skill in self.index.skills.values()
                if agent in skill.supported_agents
            ]

        # Search in raw skills
        return [
            SkillMetadata(
                id=skill.get("id", ""),
                name=skill.get("name", ""),
                description=skill.get("description", ""),
                category=skill.get("category", "general"),
                tags=skill.get("tags", []),
                supported_agents=skill.get("supported_agents", []),
                priority=skill.get("priority", "medium"),
                file_count=len(skill.get("files", [])),
            )
            for skill in self.raw_skills.get("skills", [])
            if agent in skill.get("supported_agents", [])
        ]

    def search_skills(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> List[SkillMetadata]:
        """Search for skills by query string.

        Args:
            query: Search query.
            categories: Optional filter by categories.
            tags: Optional filter by tags.

        Returns:
            List of matching SkillMetadata.
        """
        query_lower = query.lower()

        results = []
        for skill in self.raw_skills.get("skills", []):
            # Check if skill matches query
            matches = (
                query_lower in skill.get("name", "").lower()
                or query_lower in skill.get("description", "").lower()
                or any(query_lower in tag.lower() for tag in skill.get("tags", []))
            )

            if not matches:
                continue

            # Apply category filter
            if categories:
                if skill.get("category") not in categories:
                    continue

            # Apply tag filter
            if tags:
                skill_tags = skill.get("tags", [])
                if not any(tag in skill_tags for tag in tags):
                    continue

            results.append(
                SkillMetadata(
                    id=skill.get("id", ""),
                    name=skill.get("name", ""),
                    description=skill.get("description", ""),
                    category=skill.get("category", "general"),
                    tags=skill.get("tags", []),
                    supported_agents=skill.get("supported_agents", []),
                    priority=skill.get("priority", "medium"),
                    file_count=len(skill.get("files", [])),
                )
            )

        return results

    def get_categories(self) -> List[str]:
        """Get all available categories.

        Returns:
            List of category names.
        """
        if not self.index:
            self.ensure_index()

        if self.index:
            return list(self.index.categories.keys())

        categories = set()
        for skill in self.raw_skills.get("skills", []):
            categories.add(skill.get("category", "general"))

        return list(categories)

    def get_tags(self) -> List[str]:
        """Get all available tags.

        Returns:
            List of tag names.
        """
        if not self.index:
            self.ensure_index()

        if self.index:
            return list(self.index.tags.keys())

        tags = set()
        for skill in self.raw_skills.get("skills", []):
            tags.update(skill.get("tags", []))

        return list(tags)

    def refresh(self) -> SkillIndex:
        """Force refresh the index.

        Returns:
            New SkillIndex.
        """
        self.index = None
        return self.index_skills()

    def to_dict(self) -> Dict[str, Any]:
        """Convert catalog to dictionary."""
        if not self.index:
            self.ensure_index()

        return {
            "version": self.index.version if self.index else "1.0.0",
            "last_updated": self.index.last_updated if self.index else None,
            "total_skills": self.index.total_skills if self.index else 0,
            "categories": self.index.categories if self.index else {},
            "tags": self.index.tags if self.index else {},
        }


# Global catalog instance
_catalog: Optional[SkillCatalog] = None


def get_catalog() -> SkillCatalog:
    """Get or create the global skill catalog."""
    global _catalog

    if _catalog is None:
        _catalog = SkillCatalog()

    return _catalog
