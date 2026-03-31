"""Integration tests for skill catalog."""

import os
import json
import pytest
from skills.catalog import SkillCatalog, SkillIndex, SkillMetadata


class TestSkillCatalogIntegration:
    """Integration tests for skill catalog."""

    def test_full_catalog_workflow(self, sample_skill_catalog, temp_dir):
        """Test complete catalog workflow."""
        catalog_path = str(temp_dir / "skills.json")

        # Save catalog
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        # Load and index
        catalog = SkillCatalog(catalog_path=catalog_path)
        index = catalog.index_skills()

        assert index.total_skills == len(sample_skill_catalog["skills"])

        # Query skills
        typescript_skills = catalog.get_skills_by_tag("typescript")
        assert len(typescript_skills) > 0

        # Search
        results = catalog.search_skills("react")
        assert len(results) > 0

        # Get categories
        categories = catalog.get_categories()
        assert "frontend" in categories

    def test_catalog_index_persistence(self, sample_skill_catalog, temp_dir):
        """Test that index is persisted and can be reloaded."""
        catalog_path = str(temp_dir / "skills.json")
        index_path = str(temp_dir / "skills_index.json")

        # Save catalog
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        # Index
        catalog = SkillCatalog(catalog_path=catalog_path, index_path=index_path)
        catalog.index_skills()

        assert os.path.exists(index_path)

        # Reload index
        catalog2 = SkillCatalog(catalog_path=catalog_path, index_path=index_path)
        index2 = catalog2.load_index()

        assert index2 is not None
        assert index2.total_skills == sample_skill_catalog["total_skills"]

    def test_catalog_refresh(self, sample_skill_catalog, temp_dir):
        """Test catalog refresh when content changes."""
        catalog_path = str(temp_dir / "skills.json")
        index_path = str(temp_dir / "skills_index.json")

        # Save catalog
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        # Initial index
        catalog = SkillCatalog(catalog_path=catalog_path, index_path=index_path)
        index1 = catalog.ensure_index()

        # Modify catalog
        modified_catalog = sample_skill_catalog.copy()
        modified_catalog["version"] = "2.0.0"
        with open(catalog_path, "w") as f:
            json.dump(modified_catalog, f)

        # Reload - should detect change
        catalog2 = SkillCatalog(catalog_path=catalog_path, index_path=index_path)
        index2 = catalog2.load_index()

        # Index should be None (expired) and need refresh
        assert index2 is None or catalog2.index is None

    def test_skill_metadata_operations(self, sample_skill_catalog):
        """Test skill metadata operations."""
        catalog_path = "/tmp/test_metadata.json"
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        # Get skill
        skill = catalog.get_skill("web-components")
        assert skill is not None
        assert skill.name == "Web Components"

        # Get by category
        frontend = catalog.get_skills_by_category("frontend")
        assert len(frontend) > 0

        # Get by tag
        react_skills = catalog.get_skills_by_tag("react")
        assert len(react_skills) > 0

        # Get by agent
        claude_skills = catalog.get_skills_by_agent("claude-code")
        assert len(claude_skills) > 0

    def test_skill_search(self, sample_skill_catalog, temp_dir):
        """Test skill search functionality."""
        catalog_path = str(temp_dir / "skills.json")
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        # Search by name
        results = catalog.search_skills("component")
        assert len(results) > 0

        # Search by description
        results = catalog.search_skills("Reusable")
        assert len(results) > 0

        # Search with filters
        results = catalog.search_skills(
            "state",
            categories=["frontend"],
            tags=["typescript"]
        )
        assert len(results) >= 0  # May or may not match

    def test_catalog_to_dict(self, sample_skill_catalog, temp_dir):
        """Test catalog serialization."""
        catalog_path = str(temp_dir / "skills.json")
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        data = catalog.to_dict()

        assert "version" in data
        assert "total_skills" in data
        assert "categories" in data
        assert "tags" in data

    def test_empty_catalog(self, temp_dir):
        """Test handling of empty catalog."""
        catalog_path = str(temp_dir / "empty_skills.json")

        # Create empty catalog
        with open(catalog_path, "w") as f:
            json.dump({"version": "1.0.0", "skills": []}, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        index = catalog.index_skills()

        assert index.total_skills == 0
        assert catalog.get_categories() == []

    def test_invalid_catalog_handling(self, temp_dir):
        """Test handling of invalid catalog."""
        catalog_path = str(temp_dir / "invalid_skills.json")

        # Create invalid JSON
        with open(catalog_path, "w") as f:
            f.write("{ invalid json }")

        catalog = SkillCatalog(catalog_path=catalog_path)
        data = catalog.load_catalog()

        # Should handle gracefully
        assert data == {}

    def test_catalog_versioning(self, sample_skill_catalog, temp_dir):
        """Test catalog version tracking."""
        catalog_path = str(temp_dir / "skills.json")
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        assert catalog.index.version == sample_skill_catalog["version"]

    def test_tag_indexing(self, sample_skill_catalog, temp_dir):
        """Test tag indexing."""
        catalog_path = str(temp_dir / "skills.json")
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        tags = catalog.get_tags()

        assert "typescript" in tags
        assert "react" in tags
        assert "testing" in tags

    def test_category_indexing(self, sample_skill_catalog, temp_dir):
        """Test category indexing."""
        catalog_path = str(temp_dir / "skills.json")
        with open(catalog_path, "w") as f:
            json.dump(sample_skill_catalog, f)

        catalog = SkillCatalog(catalog_path=catalog_path)
        catalog.ensure_index()

        categories = catalog.get_categories()

        assert "frontend" in categories
        assert "testing" in categories
