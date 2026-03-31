"""Pytest fixtures for Programisto tests."""

import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.fixtures.sample_project import SampleProject, create_sample_log_file
from tests.fixtures.sample_skills import SAMPLE_SKILL_CATALOG
from tests.fixtures.mock_llm import MockLLMClient, mock_llm_client


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    with SampleProject() as project:
        yield project


@pytest.fixture
def sample_project_path():
    """Get path to a sample project."""
    with SampleProject() as project:
        yield project.project_path


@pytest.fixture
def sample_log_file(sample_project_path):
    """Create a sample log file."""
    return create_sample_log_file(sample_project_path)


@pytest.fixture
def sample_skill_catalog():
    """Return sample skill catalog data."""
    return SAMPLE_SKILL_CATALOG


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    return MockLLMClient("Mock LLM response")


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def config_file(temp_dir):
    """Create a sample config file."""
    config_path = temp_dir / "programisto-config.yaml"
    config_path.write_text("""
project_dir: null
llm:
  enabled: true
  api_key: test-key
  base_url: https://api.openai.com/v1
  model: test-model
  timeout: 120
tools:
  claude-code:
    enabled: true
    skills_dir: ~/.claude/skills
    activation: file-based
    version: latest
""")
    return config_path
