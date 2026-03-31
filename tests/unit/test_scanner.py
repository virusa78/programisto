"""Unit tests for project scanner."""

import os
import pytest
from scanner.project_scanner import ProjectScanner, ProjectStructure, FileAnalysis


class TestProjectScanner:
    """Tests for ProjectScanner class."""

    def test_init(self):
        """Test scanner initialization."""
        scanner = ProjectScanner()
        assert scanner.cache_dir is not None

    def test_scan_nonexistent_directory(self):
        """Test scanning a non-existent directory."""
        scanner = ProjectScanner()
        structure = scanner.scan("/nonexistent/path/that/does/not/exist")
        assert structure is not None
        assert structure.file_count == 0

    def test_scan_current_directory(self, sample_project_path):
        """Test scanning a valid directory."""
        scanner = ProjectScanner()
        structure = scanner.scan(sample_project_path)

        assert structure is not None
        assert structure.root_path == sample_project_path
        assert structure.file_count > 0
        assert "src" in structure.directories

    def test_identifies_typescript(self, sample_project_path):
        """Test TypeScript detection."""
        scanner = ProjectScanner()
        structure = scanner.scan(sample_project_path)

        assert structure.technology_stack.get("typescript") is True

    def test_identifies_react(self, sample_project_path):
        """Test React detection."""
        scanner = ProjectScanner()
        structure = scanner.scan(sample_project_path)

        assert structure.technology_stack.get("react") is True

    def test_creates_cache(self, sample_project_path):
        """Test cache creation."""
        scanner = ProjectScanner()
        scanner.scan(sample_project_path)

        assert scanner.cache_file.exists()


class TestFileAnalysis:
    """Tests for FileAnalysis class."""

    def test_file_analysis_creation(self):
        """Test creating a file analysis."""
        analysis = FileAnalysis(
            path="test.ts",
            size=1024,
            extension=".ts",
            language="typescript",
            is_source=True,
        )

        assert analysis.path == "test.ts"
        assert analysis.size == 1024
        assert analysis.language == "typescript"
        assert analysis.to_dict()["path"] == "test.ts"


class TestProjectStructure:
    """Tests for ProjectStructure class."""

    def test_structure_creation(self):
        """Test creating a project structure."""
        structure = ProjectStructure(root_path="/test")

        assert structure.root_path == "/test"
        assert structure.file_count == 0
        assert structure.directories == {}

    def test_structure_to_dict(self):
        """Test converting structure to dictionary."""
        structure = ProjectStructure(
            root_path="/test",
            file_count=10,
            total_size=1024,
        )

        data = structure.to_dict()
        assert data["root_path"] == "/test"
        assert data["file_count"] == 10
        assert data["total_size"] == 1024


class TestLogDetection:
    """Tests for log file detection."""

    def test_detects_log_files(self, sample_project_path):
        """Test log file detection."""
        # Create a log file
        log_path = os.path.join(sample_project_path, "app.log")
        with open(log_path, "w") as f:
            f.write("INFO: test log")

        scanner = ProjectScanner()
        structure = scanner.scan(sample_project_path)

        assert len(structure.log_files) >= 1
        assert any(f.path == "app.log" for f in structure.log_files)
