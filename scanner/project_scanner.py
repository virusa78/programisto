"""Project directory scanner for Programisto.

Requirement 1: Project Directory Scanning

Scans the current project directory on startup to understand the project structure
and context. Caches scan results for faster subsequent startups.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileAnalysis:
    """Analysis of a single file."""
    path: str
    size: int
    extension: str
    language: str
    is_config: bool = False
    is_source: bool = True
    is_test: bool = False
    is_log: bool = False
    content_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DirectoryAnalysis:
    """Analysis of a directory."""
    path: str
    files: List[FileAnalysis] = field(default_factory=list)
    subdirectories: List[str] = field(default_factory=list)
    total_size: int = 0
    file_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "file_count": self.file_count,
            "total_size": self.total_size,
            "subdirectories": self.subdirectories,
        }


@dataclass
class ProjectStructure:
    """Complete analysis of a project structure."""
    root_path: str
    directories: Dict[str, DirectoryAnalysis] = field(default_factory=dict)
    source_files: List[FileAnalysis] = field(default_factory=list)
    config_files: List[FileAnalysis] = field(default_factory=list)
    test_files: List[FileAnalysis] = field(default_factory=list)
    log_files: List[FileAnalysis] = field(default_factory=list)
    technology_stack: Dict[str, bool] = field(default_factory=dict)
    file_count: int = 0
    total_size: int = 0
    last_scanned: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_path": self.root_path,
            "directories": {k: v.to_dict() for k, v in self.directories.items()},
            "source_files": [f.to_dict() for f in self.source_files],
            "config_files": [f.to_dict() for f in self.config_files],
            "test_files": [f.to_dict() for f in self.test_files],
            "log_files": [f.to_dict() for f in self.log_files],
            "technology_stack": self.technology_stack,
            "file_count": self.file_count,
            "total_size": self.total_size,
            "last_scanned": self.last_scanned,
        }


class ProjectScanner:
    """Scans and analyzes project directories."""

    # Known log file patterns
    LOG_PATTERNS = {
        "*.log",
        "*.logs",
        "logs/*",
        "*-debug.log",
        "application.log",
        "app.log",
        "error.log",
        "stderr.log",
        "stdout.log",
        "npm-debug.log",
        "yarn-debug.log",
        "yarn-error.log",
        "*.log.*",
    }

    # Config file extensions
    CONFIG_EXTENSIONS = {
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".env",
        ".env.*",
        ".rc",
    }

    # Source file extensions by language
    SOURCE_EXTENSIONS = {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".py",
        ".html",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".vue",
        ".svelte",
        ".astro",
        ".php",
        ".rb",
        ".java",
        ".cs",
        ".go",
        ".rs",
        ".swift",
        ".kt",
    }

    # Test file patterns
    TEST_PATTERNS = {
        "*.test.{ts,tsx,js,jsx,py}",
        "*.spec.{ts,tsx,js,jsx,py}",
        "*_test.{ts,tsx,js,jsx,py}",
        "*_spec.{ts,tsx,js,jsx,py}",
        "tests/**/*",
        "test/**/*",
        "__tests__/**/*",
        "tests/**/**",
    }

    # Technology indicators
    TECHNOLOGY_INDICATORS = {
        "typescript": ["tsconfig.json", "package.json"],
        "react": ["package.json", "src/App.{tsx,jsx}", "react-app-env.d.ts"],
        "vue": ["vue.config.js", "src/main.{ts,js}", "vue.config.ts"],
        "angular": ["angular.json", "tsconfig.json"],
        "nodejs": ["package.json", "node_modules/.package-lock.json"],
        "python": ["requirements.txt", "pyproject.toml", "setup.py"],
        "ruby": ["Gemfile", "Gemfile.lock"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "go": ["go.mod", "go.sum"],
        "docker": ["Dockerfile", "docker-compose.{yml,yaml}"],
        "git": [".gitignore", ".git/config"],
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the scanner.

        Args:
            cache_dir: Directory for caching scan results. Defaults to .programisto/
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(".programisto")
        self.cache_file = self.cache_dir / "scan_cache.json"
        self.cache_ttl = timedelta(hours=1)

    def scan(self, project_path: Optional[str] = None) -> ProjectStructure:
        """Scan a project directory.

        Args:
            project_path: Path to scan. Defaults to current directory.

        Returns:
            ProjectStructure with complete analysis
        """
        if project_path is None:
            project_path = os.getcwd()

        project_path = os.path.abspath(project_path)

        # Check cache first
        cached = self._load_cache(project_path)
        if cached:
            logger.debug(f"Using cached scan results for {project_path}")
            return cached

        logger.info(f"Scanning project directory: {project_path}")

        structure = self._scan_directory(project_path)
        structure.last_scanned = datetime.now().isoformat()

        # Save cache
        self._save_cache(project_path, structure)

        return structure

    def _scan_directory(self, root_path: str) -> ProjectStructure:
        """Perform the actual directory scan."""
        structure = ProjectStructure(
            root_path=root_path,
            last_scanned=datetime.now().isoformat(),
        )

        self._walk_directory(root_path, structure, root_path)

        # Analyze technology stack
        self._analyze_technology(structure)

        return structure

    def _walk_directory(
        self,
        path: str,
        structure: ProjectStructure,
        root: str,
        depth: int = 0,
    ) -> None:
        """Recursively walk the directory tree."""
        try:
            rel_path = os.path.relpath(path, root)
            if rel_path == ".":
                rel_path = ""

            dir_analysis = DirectoryAnalysis(path=path)

            # Get all entries in directory
            entries = []
            try:
                entries = os.listdir(path)
            except PermissionError:
                logger.warning(f"Permission denied: {path}")
                structure.directories[rel_path] = dir_analysis
                return

            for entry in entries:
                entry_path = os.path.join(path, entry)

                if os.path.isdir(entry_path):
                    # Skip common non-essential directories
                    if entry in {
                        "node_modules",
                        "__pycache__",
                        ".git",
                        ".cache",
                        ".vscode",
                        ".idea",
                        "venv",
                        ".venv",
                        "dist",
                        "build",
                        "coverage",
                        ".next",
                        "next-env.d.ts",
                    }:
                        continue

                    dir_analysis.subdirectories.append(
                        os.path.relpath(entry_path, root)
                    )
                    self._walk_directory(entry_path, structure, root, depth + 1)

                elif os.path.isfile(entry_path):
                    file_analysis = self._analyze_file(entry_path, root)

                    if file_analysis.is_log:
                        structure.log_files.append(file_analysis)
                    elif file_analysis.is_test:
                        structure.test_files.append(file_analysis)
                    elif file_analysis.is_config:
                        structure.config_files.append(file_analysis)
                    elif file_analysis.is_source:
                        structure.source_files.append(file_analysis)

                    dir_analysis.files.append(file_analysis)
                    dir_analysis.file_count += 1
                    dir_analysis.total_size += file_analysis.size

            structure.directories[rel_path] = dir_analysis
            structure.file_count += dir_analysis.file_count
            structure.total_size += dir_analysis.total_size

        except Exception as e:
            logger.error(f"Error scanning directory {path}: {e}")

    def _analyze_file(self, file_path: str, root: str) -> FileAnalysis:
        """Analyze a single file."""
        rel_path = os.path.relpath(file_path, root)
        ext = os.path.splitext(file_path)[1].lower()
        size = os.path.getsize(file_path)

        # Determine file type
        is_log = self._is_log_file(rel_path, ext)
        is_config = ext in self.CONFIG_EXTENSIONS or self._is_config_file(rel_path)
        is_test = self._is_test_file(rel_path, ext)
        is_source = ext in self.SOURCE_EXTENSIONS and not is_test

        # Calculate content hash (first 1KB for performance)
        content_hash = self._calculate_hash(file_path)

        # Determine language
        language = self._get_language(ext)

        return FileAnalysis(
            path=rel_path,
            size=size,
            extension=ext,
            language=language,
            is_config=is_config,
            is_source=is_source,
            is_test=is_test,
            is_log=is_log,
            content_hash=content_hash,
        )

    def _is_log_file(self, rel_path: str, ext: str) -> bool:
        """Check if a file is a log file."""
        basename = os.path.basename(rel_path).lower()

        # Check extension
        if ext in {".log", ".logs"}:
            return True

        # Check filename patterns
        for pattern in self.LOG_PATTERNS:
            if self._match_pattern(rel_path, pattern):
                return True

        # Check common log file names
        log_names = {
            "application.log",
            "app.log",
            "error.log",
            "stderr.log",
            "stdout.log",
            "npm-debug.log",
            "yarn-debug.log",
            "yarn-error.log",
        }
        if basename in log_names:
            return True

        return False

    def _is_config_file(self, rel_path: str) -> bool:
        """Check if a file is a config file by name."""
        basename = os.path.basename(rel_path)
        config_names = {
            "package.json",
            "tsconfig.json",
            "jsconfig.json",
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Pipfile",
            "Gemfile",
            "Cargo.toml",
            "go.mod",
            "Dockerfile",
            ".env",
            ".gitignore",
        }
        return basename in config_names

    def _is_test_file(self, rel_path: str, ext: str) -> bool:
        """Check if a file is a test file."""
        basename = os.path.basename(rel_path)

        # Check test patterns
        test_patterns = {
            "*.test.ts",
            "*.test.tsx",
            "*.test.js",
            "*.test.jsx",
            "*.test.py",
            "*.spec.ts",
            "*.spec.tsx",
            "*.spec.js",
            "*.spec.jsx",
            "*.spec.py",
            "*_test.py",
            "*_test.ts",
            "*_test.js",
            "*_spec.py",
            "*_spec.ts",
            "*_spec.js",
        }

        for pattern in test_patterns:
            if self._match_pattern(basename, pattern):
                return True

        # Check test directory
        if "test" in rel_path.lower().split(os.sep):
            return True

        return False

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Simple glob pattern matching."""
        import fnmatch

        basename = os.path.basename(path)
        return fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(
            path, pattern
        )

    def _calculate_hash(self, file_path: str, chunk_size: int = 1024) -> str:
        """Calculate a hash of the file content."""
        try:
            hasher = hashlib.md5()
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def _get_language(self, ext: str) -> str:
        """Get the programming language for a file extension."""
        language_map = {
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".py": "python",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".vue": "vue",
            ".svelte": "svelte",
            ".astro": "astro",
            ".php": "php",
            ".rb": "ruby",
            ".java": "java",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
        }
        return language_map.get(ext, "unknown")

    def _analyze_technology(self, structure: ProjectStructure) -> None:
        """Detect the technology stack of the project."""
        # Check for technology indicator files
        all_files = [
            f.path for f in structure.source_files
        ] + [f.path for f in structure.config_files]

        for tech, indicators in self.TECHNOLOGY_INDICATORS.items():
            for indicator in indicators:
                if any(self._match_pattern(f, indicator) for f in all_files):
                    structure.technology_stack[tech] = True
                    break

    def _load_cache(self, project_path: str) -> Optional[ProjectStructure]:
        """Load cached scan results if valid."""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r") as f:
                cache_data = json.load(f)

            # Check if cache is for this project
            cached_path = cache_data.get("project_path")
            if cached_path != project_path:
                logger.debug(
                    f"Cache is for different project: {cached_path} != {project_path}"
                )
                return None

            # Check cache age
            last_scanned = cache_data.get("last_scanned")
            if last_scanned:
                scan_time = datetime.fromisoformat(last_scanned)
                if datetime.now() - scan_time > self.cache_ttl:
                    logger.debug("Cache has expired")
                    return None

            # Convert to ProjectStructure
            return self._dict_to_structure(cache_data)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _save_cache(self, project_path: str, structure: ProjectStructure) -> None:
        """Save scan results to cache."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            cache_data = structure.to_dict()
            cache_data["project_path"] = project_path

            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _dict_to_structure(self, data: Dict[str, Any]) -> ProjectStructure:
        """Convert dictionary back to ProjectStructure."""
        structure = ProjectStructure(
            root_path=data.get("root_path", ""),
            last_scanned=data.get("last_scanned"),
            technology_stack=data.get("technology_stack", {}),
            file_count=data.get("file_count", 0),
            total_size=data.get("total_size", 0),
        )

        # Reconstruct directories
        for path, dir_data in data.get("directories", {}).items():
            dir_analysis = DirectoryAnalysis(
                path=path,
                file_count=dir_data.get("file_count", 0),
                total_size=dir_data.get("total_size", 0),
                subdirectories=dir_data.get("subdirectories", []),
            )
            structure.directories[path] = dir_analysis

        # Reconstruct file lists
        for file_data in data.get("source_files", []):
            structure.source_files.append(
                FileAnalysis(
                    path=file_data["path"],
                    size=file_data["size"],
                    extension=file_data["extension"],
                    language=file_data["language"],
                    is_config=file_data.get("is_config", False),
                    is_source=file_data.get("is_source", True),
                    is_test=file_data.get("is_test", False),
                    is_log=file_data.get("is_log", False),
                    content_hash=file_data.get("content_hash", ""),
                )
            )

        for file_data in data.get("config_files", []):
            structure.config_files.append(
                FileAnalysis(
                    path=file_data["path"],
                    size=file_data["size"],
                    extension=file_data["extension"],
                    language=file_data["language"],
                    is_config=file_data.get("is_config", False),
                    is_source=file_data.get("is_source", True),
                    is_test=file_data.get("is_test", False),
                    is_log=file_data.get("is_log", False),
                    content_hash=file_data.get("content_hash", ""),
                )
            )

        for file_data in data.get("test_files", []):
            structure.test_files.append(
                FileAnalysis(
                    path=file_data["path"],
                    size=file_data["size"],
                    extension=file_data["extension"],
                    language=file_data["language"],
                    is_config=file_data.get("is_config", False),
                    is_source=file_data.get("is_source", True),
                    is_test=file_data.get("is_test", False),
                    is_log=file_data.get("is_log", False),
                    content_hash=file_data.get("content_hash", ""),
                )
            )

        for file_data in data.get("log_files", []):
            structure.log_files.append(
                FileAnalysis(
                    path=file_data["path"],
                    size=file_data["size"],
                    extension=file_data["extension"],
                    language=file_data["language"],
                    is_config=file_data.get("is_config", False),
                    is_source=file_data.get("is_source", True),
                    is_test=file_data.get("is_test", False),
                    is_log=file_data.get("is_log", False),
                    content_hash=file_data.get("content_hash", ""),
                )
            )

        return structure

    def create_project_template(self, project_path: str) -> None:
        """Create a new project structure template.

        Requirement 1: If no project directory exists, create a new project
        structure template.
        """
        project_path = os.path.abspath(project_path)
        Path(project_path).mkdir(parents=True, exist_ok=True)

        # Create basic web project structure
        directories = [
            "src",
            "src/components",
            "src/hooks",
            "src/utils",
            "src/types",
            "src/api",
            "src/store",
            "tests",
            ".github/workflows",
        ]

        files = {
            "README.md": "# Project\n\nA new web project.\n",
            ".gitignore": """# Dependencies
node_modules/
.pip-cache/

# Environment
.env
.env.local

# Build
dist/
build/
.next/

# IDE
.vscode/
.idea/

# Logs
*.log
logs/

# OS
.DS_Store
""",
            "package.json": """{
  "name": "new-project",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
""",
            "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
""",
            "src/main.tsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
            "src/App.tsx": """function App() {
  return (
    <div className="app">
      <h1>Welcome to Programisto</h1>
    </div>
  )
}

export default App
""",
            "src/index.css": """* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
""",
        }

        # Create directories
        for directory in directories:
            Path(os.path.join(project_path, directory)).mkdir(
                parents=True, exist_ok=True
            )

        # Create files
        for filename, content in files.items():
            filepath = os.path.join(project_path, filename)
            Path(filepath).write_text(content)

        logger.info(f"Created project template at {project_path}")
