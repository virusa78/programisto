"""Engineering harness generator for Programisto.

Requirement 5: Engineering Harness Generation

Generates a set of engineering harness tools including scripts for common
development tasks and framework-specific tools.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from scanner.project_scanner import ProjectStructure


@dataclass
class HarnessTool:
    """A single tool in the engineering harness."""

    id: str
    name: str
    description: str
    type: str  # script, config, hook, etc.
    content: str
    file_path: str
    executable: bool = False
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "file_path": self.file_path,
            "executable": self.executable,
            "dependencies": self.dependencies,
            "tags": self.tags,
        }


class HarnessGenerator:
    """Generates engineering harness tools."""

    # Common scripts to include
    BASIC_SCRIPTS = {
        "setup": {
            "name": "Setup Script",
            "description": "Initial project setup and dependency installation",
            "type": "script",
            "executable": True,
        },
        "dev": {
            "name": "Development Server",
            "description": "Start development server",
            "type": "script",
            "executable": True,
        },
        "build": {
            "name": "Build Script",
            "description": "Build the project for production",
            "type": "script",
            "executable": True,
        },
        "test": {
            "name": "Test Runner",
            "description": "Run test suite",
            "type": "script",
            "executable": True,
        },
        "lint": {
            "name": "Linter",
            "description": "Run code linter",
            "type": "script",
            "executable": True,
        },
    }

    def __init__(self, project_structure: Optional[ProjectStructure] = None):
        """Initialize the harness generator.

        Args:
            project_structure: Optional project structure for context.
        """
        self.project_structure = project_structure
        self.tools: Dict[str, HarnessTool] = {}
        self._load_basic_scripts()

    def _load_basic_scripts(self) -> None:
        """Load basic script templates."""
        # Setup script
        self.tools["setup"] = HarnessTool(
            id="setup",
            **self.BASIC_SCRIPTS["setup"],
            content="""#!/bin/bash
# Setup script for the project

set -e

echo "Setting up project..."

# Check for package manager
if command -v npm &> /dev/null; then
    echo "Installing dependencies with npm..."
    npm install
elif command -v pnpm &> /dev/null; then
    echo "Installing dependencies with pnpm..."
    pnpm install
elif command -v yarn &> /dev/null; then
    echo "Installing dependencies with yarn..."
    yarn install
else
    echo "Error: No package manager found"
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env 2>/dev/null || touch .env
    echo "# Environment variables configured" >> .env
fi

echo "Setup complete!"
""",
            file_path="scripts/setup.sh",
            dependencies=[],
            tags=["setup", "installation"],
        )

        # Dev script
        self.tools["dev"] = HarnessTool(
            id="dev",
            **self.BASIC_SCRIPTS["dev"],
            content="""#!/bin/bash
# Development server script

set -e

echo "Starting development server..."

# Check for package manager
if command -v npm &> /dev/null; then
    npm run dev
elif command -v pnpm &> /dev/null; then
    pnpm dev
elif command -v yarn &> /dev/null; then
    yarn dev
else
    echo "Error: No package manager found"
    exit 1
fi
""",
            file_path="scripts/dev.sh",
            dependencies=[],
            tags=["development", "server"],
        )

        # Build script
        self.tools["build"] = HarnessTool(
            id="build",
            **self.BASIC_SCRIPTS["build"],
            content="""#!/bin/bash
# Build script for production

set -e

echo "Building project..."

# Check for package manager
if command -v npm &> /dev/null; then
    npm run build
elif command -v pnpm &> /dev/null; then
    pnpm build
elif command -v yarn &> /dev/null; then
    yarn build
else
    echo "Error: No package manager found"
    exit 1
fi

echo "Build complete!"
""",
            file_path="scripts/build.sh",
            dependencies=[],
            tags=["build", "production"],
        )

        # Test script
        self.tools["test"] = HarnessTool(
            id="test",
            **self.BASIC_SCRIPTS["test"],
            content="""#!/bin/bash
# Test runner script

set -e

echo "Running tests..."

# Check for package manager
if command -v npm &> /dev/null; then
    npm run test
elif command -v pnpm &> /dev/null; then
    pnpm test
elif command -v yarn &> /dev/null; then
    yarn test
else
    echo "Error: No package manager found"
    exit 1
fi
""",
            file_path="scripts/test.sh",
            dependencies=[],
            tags=["testing", "test"],
        )

        # Lint script
        self.tools["lint"] = HarnessTool(
            id="lint",
            **self.BASIC_SCRIPTS["lint"],
            content="""#!/bin/bash
# Linter script

set -e

echo "Running linter..."

# Check for package manager
if command -v npm &> /dev/null; then
    npm run lint
elif command -v pnpm &> /dev/null; then
    pnpm lint
elif command -v yarn &> /dev/null; then
    yarn lint
else
    echo "Error: No package manager found"
    exit 1
fi
""",
            file_path="scripts/lint.sh",
            dependencies=[],
            tags=["lint", "code-quality"],
        )

        # Format script
        self.tools["format"] = HarnessTool(
            id="format",
            name="Formatter",
            description="Format code with Prettier or similar",
            type="script",
            executable=True,
            file_path="scripts/format.sh",
            content="""#!/bin/bash
# Code formatter script

set -e

echo "Formatting code..."

# Check for package manager
if command -v npm &> /dev/null; then
    npm run format
elif command -v pnpm &> /dev/null; then
    pnpm format
elif command -v yarn &> /dev/null; then
    yarn format
else
    echo "Error: No package manager found"
    exit 1
fi
""",
            dependencies=[],
            tags=["format", "code-quality"],
        )

        # Git hooks setup
        self.tools["git-hooks"] = HarnessTool(
            id="git-hooks",
            name="Git Hooks Setup",
            description="Setup pre-commit and pre-push hooks",
            type="hook",
            executable=False,
            file_path="scripts/git-hooks/setup.sh",
            content="""#!/bin/bash
# Setup git hooks

set -e

HOOKS_DIR=".githooks"
GIT_DIR=".git"

# Create hooks directory
mkdir -p "$HOOKS_DIR"

# Pre-commit hook
cat > "$GIT_DIR/hooks/pre-commit" << 'EOF'
#!/bin/bash
set -e

echo "Running pre-commit checks..."

# Run linter
npm run lint || exit 1

# Run tests
npm run test -- --bail || exit 1

echo "Pre-commit checks passed!"
EOF

# Pre-push hook
cat > "$GIT_DIR/hooks/pre-push" << 'EOF'
#!/bin/bash
set -e

echo "Running pre-push checks..."

# Run full test suite
npm run test -- --coverage || exit 1

echo "Pre-push checks passed!"
EOF

# Make hooks executable
chmod +x "$GIT_DIR/hooks/pre-commit"
chmod +x "$GIT_DIR/hooks/pre-push"

echo "Git hooks installed successfully!"
""",
            dependencies=[],
            tags=["git", "hooks", "automation"],
        )

    def generate_harness(
        self,
        project_structure: Optional[ProjectStructure] = None,
        include_framework_tools: bool = True,
    ) -> List[HarnessTool]:
        """Generate engineering harness tools.

        Args:
            project_structure: Project structure for context.
            include_framework_tools: Include framework-specific tools.

        Returns:
            List of harness tools.
        """
        if project_structure:
            self.project_structure = project_structure

        # Start with basic tools
        tools = list(self.tools.values())

        # Add framework-specific tools if detected
        if include_framework_tools and self.project_structure:
            tools.extend(self._generate_framework_tools())

        return tools

    def _generate_framework_tools(self) -> List[HarnessTool]:
        """Generate framework-specific tools based on detected tech."""
        if not self.project_structure:
            return []

        tech_stack = self.project_structure.technology_stack
        tools = []

        # React/Vite tools
        if tech_stack.get("react") or tech_stack.get("typescript"):
            tools.append(HarnessTool(
                id="vite-config",
                name="Vite Config",
                description="Vite configuration for React/TypeScript projects",
                type="config",
                executable=False,
                file_path="vite.config.ts",
                content="""import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
    },
  },
  server: {
    port: 3000,
    open: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
""",
                dependencies=["vite", "@vitejs/plugin-react"],
                tags=["vite", "react", "config"],
            ))

            tools.append(HarnessTool(
                id="eslint-config",
                name="ESLint Config",
                description="ESLint configuration for React/TypeScript",
                type="config",
                executable=False,
                file_path=".eslintrc.cjs",
                content="""module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
""",
                dependencies=["eslint", "@typescript-eslint/eslint-plugin"],
                tags=["eslint", "lint", "config"],
            ))

        # Python tools
        if tech_stack.get("python"):
            tools.append(HarnessTool(
                id="pytest-config",
                name="Pytest Config",
                description="Pytest configuration",
                type="config",
                executable=False,
                file_path="pytest.ini",
                content="""[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
""",
                dependencies=["pytest"],
                tags=["pytest", "testing", "config"],
            ))

        # Docker tools
        if tech_stack.get("docker"):
            tools.append(HarnessTool(
                id="docker-compose",
                name="Docker Compose",
                description="Docker Compose configuration",
                type="config",
                executable=False,
                file_path="docker-compose.yml",
                content="""version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - CHOKIDAR_USEPOLLING=true
    volumes:
      - .:/app
      - /app/node_modules
    command: npm run dev

  # Add database services as needed
  # postgres:
  #   image: postgres:15
  #   environment:
  #     POSTGRES_DB: app
  #     POSTGRES_USER: app
  #     POSTGRES_PASSWORD: secret
  #   ports:
  #     - "5432:5432"
""",
                dependencies=["docker", "docker-compose"],
                tags=["docker", "containers"],
            ))

        # TypeScript tools
        if tech_stack.get("typescript"):
            tools.append(HarnessTool(
                id="prettier-config",
                name="Prettier Config",
                description="Prettier code formatting configuration",
                type="config",
                executable=False,
                file_path=".prettierrc",
                content="""{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
""",
                dependencies=["prettier"],
                tags=["prettier", "formatting"],
            ))

        # Git hooks for all projects
        tools.append(HarnessTool(
            id="commitlint-config",
            name="Commitlint Config",
            description="Conventional commits configuration",
            type="config",
            executable=False,
            file_path=".commitlintrc.json",
            content="""{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [
      2,
      "always",
      [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "build",
        "ci",
        "chore",
        "revert"
      ]
    ]
  }
}
""",
            dependencies=["@commitlint/cli", "@commitlint/config-conventional"],
            tags=["commitlint", "conventional-commits"],
        ))

        return tools

    def generate_complete_harness(self) -> Dict[str, Any]:
        """Generate a complete engineering harness.

        Returns:
            Dictionary with all harness tools and metadata.
        """
        tools = self.generate_harness()

        return {
            "generated_at": datetime.now().isoformat(),
            "tools": [tool.to_dict() for tool in tools],
            "count": len(tools),
            "frameworks": list(self.project_structure.technology_stack.keys())
            if self.project_structure
            else [],
        }

    def save_harness(
        self,
        output_dir: str = ".",
        prefix: str = "harness_",
    ) -> List[str]:
        """Save all harness tools to files.

        Args:
            output_dir: Directory to save files to.
            prefix: Prefix for file names.

        Returns:
            List of saved file paths.
        """
        tools = self.generate_harness()
        saved_paths = []

        for tool in tools:
            # Create directory if needed
            tool_dir = os.path.dirname(os.path.join(output_dir, tool.file_path))
            os.makedirs(tool_dir, exist_ok=True)

            # Write file
            filepath = os.path.join(output_dir, tool.file_path)
            with open(filepath, "w") as f:
                f.write(tool.content)

            # Make executable scripts executable
            if tool.executable:
                os.chmod(filepath, 0o755)

            saved_paths.append(filepath)

        return saved_paths

    def get_best_practices(self) -> List[str]:
        """Get best practices based on project context.

        Returns:
            List of best practice recommendations.
        """
        practices = [
            "Always write tests for new features and bug fixes",
            "Keep components small and focused on a single responsibility",
            "Use TypeScript for type safety",
            "Follow consistent code formatting with Prettier",
            "Write meaningful commit messages following conventional commits",
            "Document public APIs with JSDoc comments",
            "Use environment variables for configuration",
            "Implement error boundaries for graceful error handling",
            "Use lazy loading for code splitting",
            "Implement proper authentication flow with token refresh",
        ]

        # Add framework-specific practices
        if self.project_structure:
            tech_stack = self.project_structure.technology_stack

            if tech_stack.get("react"):
                practices.extend([
                    "Use functional components with hooks",
                    "Memoize expensive computations with useMemo and useCallback",
                    "Avoid inline object/arrow function props in render",
                    "Use React.lazy for code splitting",
                ])

            if tech_stack.get("typescript"):
                practices.extend([
                    "Use 'strict: true' in tsconfig.json",
                    "Define interfaces for all public APIs",
                    "Use type guards for type narrowing",
                    "Avoid 'any' type - use 'unknown' if type is unclear",
                ])

        return practices

    def to_dict(self) -> Dict[str, Any]:
        """Convert harness to dictionary format."""
        return {
            "generated_at": datetime.now().isoformat(),
            "tools": [tool.to_dict() for tool in self.tools.values()],
            "count": len(self.tools),
        }


# Global generator instance
_generator: Optional[HarnessGenerator] = None


def get_generator(
    project_structure: Optional[ProjectStructure] = None,
) -> HarnessGenerator:
    """Get or create the global harness generator."""
    global _generator

    if _generator is None:
        _generator = HarnessGenerator(project_structure)

    return _generator
