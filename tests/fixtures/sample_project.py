"""Sample project fixtures for testing."""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional


class SampleProject:
    """Creates a sample project structure for testing."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize with optional base directory."""
        self.base_dir = base_dir
        self.temp_dir: Optional[str] = None
        self.project_path: Optional[str] = None

    def create(
        self,
        name: str = "test-project",
        with_typescript: bool = True,
        with_react: bool = True,
    ) -> str:
        """Create a sample project.

        Args:
            name: Project name.
            with_typescript: Include TypeScript config.
            with_react: Include React files.

        Returns:
            Path to the created project.
        """
        self.temp_dir = tempfile.mkdtemp(prefix="programisto_test_")
        self.project_path = os.path.join(self.temp_dir, name)
        os.makedirs(self.project_path)

        # Create directory structure
        dirs = [
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

        for directory in dirs:
            os.makedirs(os.path.join(self.project_path, directory), exist_ok=True)

        # Create basic files
        files = {
            "README.md": f"# {name}\n\nA test project for Programisto.",
            ".gitignore": """node_modules/
.env
dist/
build/
*.log
""",
        }

        if with_typescript:
            files.update({
                "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "strict": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
""",
            })

        if with_react:
            files.update({
                "package.json": """{
  "name": "test-project",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
""",
                "src/main.tsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
                "src/App.tsx": """function App() {
  return <div className="app"><h1>Hello</h1></div>
}

export default App
""",
            })

        # Create files
        for filename, content in files.items():
            filepath = os.path.join(self.project_path, filename)
            with open(filepath, "w") as f:
                f.write(content)

        return self.project_path

    def cleanup(self) -> None:
        """Clean up the temporary project."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
            self.project_path = None

    def __enter__(self) -> "SampleProject":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.cleanup()


def create_sample_log_file(
    project_path: str,
    filename: str = "app.log",
    entries: Optional[Dict[str, int]] = None,
) -> str:
    """Create a sample log file.

    Args:
        project_path: Project directory.
        filename: Log file name.
        entries: Dict of log levels and counts.

    Returns:
        Path to the log file.
    """
    if entries is None:
        entries = {"error": 5, "warning": 10, "info": 50, "debug": 100}

    log_path = os.path.join(project_path, "logs", filename)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    import random
    from datetime import datetime, timedelta

    levels = ["ERROR", "WARNING", "INFO", "DEBUG"]
    messages = {
        "ERROR": [
            "Database connection failed",
            "Authentication error",
            "File not found",
        ],
        "WARNING": [
            "Deprecated API usage",
            "Slow query detected",
            "Cache miss",
        ],
        "INFO": [
            "User logged in",
            "Request processed",
            "Task completed",
        ],
        "DEBUG": [
            "Variable state: x=5",
            "Entering function foo",
            "Cache key: abc123",
        ],
    }

    lines = []
    base_time = datetime.now() - timedelta(hours=2)

    total = sum(entries.values())
    for i in range(total):
        level = random.choice(levels)
        count = sum(1 for lvl, cnt in entries.items() if lvl == level.lower())
        if random.random() * total < count:
            msg = random.choice(messages[level])
            timestamp = base_time + timedelta(seconds=i * 60)
            line = f"{timestamp.isoformat()} [{level}] {msg}\n"
            lines.append(line)

    with open(log_path, "w") as f:
        f.writelines(lines)

    return log_path
