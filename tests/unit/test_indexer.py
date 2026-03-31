"""Unit tests for skill catalog indexer."""

import json
import os
import pytest
from skills.catalog import SkillCatalog, SkillIndex, SkillMetadata


class TestSkillCatalog:
    """Tests for SkillCatalog class."""

    def test_init(self):
        """Test catalog initialization."""
        catalog = SkillCatalog()
        assert catalog.catalog_path == "skills_catalog/skills.json"
        assert catalog.index is None

    def test_load_nonexistent_catalog(self):
        """Test loading a non-existent catalog."""
        catalog = SkillCatalog(catalog_path="/nonexistent/skills.json")
        data = catalog.load_catalog()
        assert data == {}

    def test_index_skills(self, sample_skill_catalog):
        """Test indexing skills."""
        # Save sample catalog
        catalog_path = "/tmp/test_skills.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        index = catalog.index_skills()

        assert index.total_skills == len(sample_skill_catalog["skills"])
        assert "web-components" in index.skills
        assert "react-hooks" in index.skills

    def test_get_skill(self, sample_skill_catalog):
        """Test getting a skill by ID."""
        catalog_path = "/tmp/test_skills2.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        skill = catalog.get_skill("web-components")
        assert skill is not None
        assert skill.name == "Web Components"

    def test_get_skills_by_category(self, sample_skill_catalog):
        """Test getting skills by category."""
        catalog_path = "/tmp/test_skills3.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        frontend_skills = catalog.get_skills_by_category("frontend")
        assert len(frontend_skills) > 0
        assert all(s.category == "frontend" for s in frontend_skills)

    def test_get_skills_by_tag(self, sample_skill_catalog):
        """Test getting skills by tag."""
        catalog_path = "/tmp/test_skills4.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        typescript_skills = catalog.get_skills_by_tag("typescript")
        assert len(typescript_skills) > 0

    def test_get_skills_by_agent(self, sample_skill_catalog):
        """Test getting skills by supported agent."""
        catalog_path = "/tmp/test_skills5.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        claude_skills = catalog.get_skills_by_agent("claude-code")
        assert len(claude_skills) > 0

    def test_search_skills(self, sample_skill_catalog):
        """Test searching skills."""
        catalog_path = "/tmp/test_skills6.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        results = catalog.search_skills("react")
        assert len(results) > 0
        assert any("react" in s.name.lower() for s in results)

    def test_get_categories(self, sample_skill_catalog):
        """Test getting all categories."""
        catalog_path = "/tmp/test_skills7.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        categories = catalog.get_categories()
        assert "frontend" in categories
        assert "testing" in categories

    def test_refresh_index(self, sample_skill_catalog):
        """Test refreshing the index."""
        catalog_path = "/tmp/test_skills8.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        old_hash = catalog.index.index_hash
        new_index = catalog.refresh()
        assert new_index.index_hash == old_hash  # Same content

    def test_to_dict(self, sample_skill_catalog):
        """Test converting catalog to dictionary."""
        catalog_path = "/tmp/test_skills9.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        data = catalog.to_dict()
        assert data["total_skills"] == len(sample_skill_catalog["skills"])
        assert "frontend" in data["categories"]


class TestSkillMetadata:
    """Tests for SkillMetadata class."""

    def test_metadata_creation(self):
        """Test creating skill metadata."""
        metadata = SkillMetadata(
            id="test-skill",
            name="Test Skill",
            description="A test skill",
            category="test",
            tags=["test", "unit"],
        )

        assert metadata.id == "test-skill"
        assert metadata.name == "Test Skill"
        assert "test" in metadata.tags

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = SkillMetadata(
            id="test-skill",
            name="Test Skill",
            description="A test skill",
            category="test",
        )

        data = metadata.to_dict()
        assert data["id"] == "test-skill"
        assert data["name"] == "Test Skill"


class TestSkillIndex:
    """Tests for SkillIndex class."""

    def test_index_creation(self):
        """Test creating a skill index."""
        index = SkillIndex()
        assert index.total_skills == 0
        assert index.skills == {}

    def test_index_from_dict(self):
        """Test creating index from dictionary."""
        data = {
            "version": "1.0.0",
            "last_updated": "2026-03-31",
            "skills": {
                "test": {
                    "id": "test",
                    "name": "Test",
                    "description": "Test skill",
                    "category": "test",
                    "tags": [],
                    "supported_agents": [],
                    "priority": "medium",
                    "file_count": 0,
                    "last_indexed": None,
                    "content_hash": "",
                }
            },
            "categories": {"test": ["test"]},
            "tags": {},
            "total_skills": 1,
            "index_hash": "abc123",
        }

        index = SkillIndex.from_dict(data)
        assert index.version == "1.0.0"
        assert "test" in index.skills
        assert index.total_skills == 1

    def test_index_to_dict(self):
        """Test converting index to dictionary."""
        index = SkillIndex(
            version="1.0.0",
            last_updated="2026-03-31",
            total_skills=5,
        )

        data = index.to_dict()
        assert data["version"] == "1.0.0"
        assert data["total_skills"] == 5
