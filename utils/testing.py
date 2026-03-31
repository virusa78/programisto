"""Testing utilities for Programisto.

Requirement 7: Testing and Dry-Run Execution

Provides support for testing and dry-run execution of potentially
destructive operations.
"""

import os
import shutil
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import tempfile


@dataclass
class DryRunResult:
    """Result of a dry-run operation."""

    success: bool
    changes: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "changes": self.changes,
            "warnings": self.warnings,
            "summary": self.summary,
        }


@dataclass
class TestResult:
    """Result of a test execution."""

    passed: bool
    total: int
    failures: int
    errors: int
    duration: float
    output: str = ""
    failures_list: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "total": self.total,
            "failures": self.failures,
            "errors": self.errors,
            "duration": self.duration,
            "output": self.output,
        }


class DryRunExecutor:
    """Executes operations in dry-run mode."""

    def __init__(self, enabled: bool = False):
        """Initialize dry-run executor.

        Args:
            enabled: Whether dry-run is enabled.
        """
        self.enabled = enabled
        self.changes: List[Dict[str, Any]] = []
        self.warnings: List[str] = []

    def execute(
        self,
        operation: str,
        target: str,
        action: Callable[[], Any],
        *args,
        **kwargs,
    ) -> Any:
        """Execute an operation, simulating if dry-run is enabled.

        Args:
            operation: Type of operation (create, delete, modify, etc.).
            target: Target of the operation.
            action: The action function to execute.
            *args: Arguments to pass to the action.
            **kwargs: Keyword arguments to pass to the action.

        Returns:
            Result of the action (or None in dry-run for destructive ops).
        """
        if self.enabled:
            # Record the change
            change = {
                "operation": operation,
                "target": target,
                "timestamp": datetime.now().isoformat(),
                "will_execute": True,
            }
            self.changes.append(change)

            # Log the change
            print(f"[DRY-RUN] {operation.upper()}: {target}")

            # For destructive operations, don't actually execute
            if operation in ("delete", "remove", "overwrite"):
                self.warnings.append(
                    f"Would {operation} {target} but dry-run is enabled"
                )
                return None

            # For non-destructive operations, still simulate
            # (could add more sophisticated simulation logic here)
            return None

        # Normal execution
        return action(*args, **kwargs)

    def execute_file_create(
        self,
        filepath: str,
        content: str,
    ) -> Optional[str]:
        """Simulate creating a file.

        Args:
            filepath: Path to create.
            content: Content to write.

        Returns:
            Path if dry-run, None if dry-run for destructive, or actual result.
        """
        def create_file():
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(content)
            return filepath

        return self.execute("create", filepath, create_file)

    def execute_file_delete(
        self,
        filepath: str,
    ) -> Optional[str]:
        """Simulate deleting a file.

        Args:
            filepath: Path to delete.

        Returns:
            Path if dry-run, None if dry-run for destructive.
        """
        def delete_file():
            if os.path.exists(filepath):
                os.remove(filepath)
            return filepath

        return self.execute("delete", filepath, delete_file)

    def execute_file_modify(
        self,
        filepath: str,
        new_content: str,
    ) -> Optional[str]:
        """Simulate modifying a file.

        Args:
            filepath: Path to modify.
            new_content: New content to write.

        Returns:
            Path if dry-run, None if dry-run for destructive.
        """
        def modify_file():
            with open(filepath, "w") as f:
                f.write(new_content)
            return filepath

        return self.execute("modify", filepath, modify_file)

    def execute_directory_create(
        self,
        dirpath: str,
    ) -> Optional[str]:
        """Simulate creating a directory.

        Args:
            dirpath: Path to create.

        Returns:
            Path if dry-run, None if dry-run for destructive.
        """
        def create_directory():
            os.makedirs(dirpath, exist_ok=True)
            return dirpath

        return self.execute("create", dirpath, create_directory)

    def execute_directory_delete(
        self,
        dirpath: str,
    ) -> Optional[str]:
        """Simulate deleting a directory.

        Args:
            dirpath: Path to delete.

        Returns:
            Path if dry-run, None if dry-run for destructive.
        """
        def delete_directory():
            if os.path.exists(dirpath):
                shutil.rmtree(dirpath)
            return dirpath

        return self.execute("delete", dirpath, delete_directory)

    def get_summary(self) -> str:
        """Get a summary of all changes recorded.

        Returns:
            Summary string.
        """
        if not self.changes:
            return "No changes recorded"

        lines = [
            "Dry-Run Summary",
            "===============",
            f"Total changes: {len(self.changes)}",
            "",
        ]

        # Group by operation type
        by_operation: Dict[str, List[Dict]] = {}
        for change in self.changes:
            op = change["operation"]
            if op not in by_operation:
                by_operation[op] = []
            by_operation[op].append(change)

        for op, changes in by_operation.items():
            lines.append(f"{op.upper()} ({len(changes)}):")
            for change in changes:
                lines.append(f"  - {change['target']}")
            lines.append("")

        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset the dry-run state."""
        self.changes = []
        self.warnings = []

    def as_result(self) -> DryRunResult:
        """Convert dry-run state to DryRunResult."""
        return DryRunResult(
            success=True,
            changes=self.changes,
            warnings=self.warnings,
            summary=self.get_summary(),
        )


class TestRunner:
    """Runs tests for a project."""

    def __init__(self, project_path: str):
        """Initialize test runner.

        Args:
            project_path: Path to the project.
        """
        self.project_path = project_path
        self.test_commands = {
            "npm": ["npm", "test"],
            "yarn": ["yarn", "test"],
            "pnpm": ["pnpm", "test"],
            "pytest": ["pytest"],
            "python": ["python", "-m", "pytest"],
            "jest": ["npx", "jest"],
            "mocha": ["npx", "mocha"],
        }

    def detect_test_command(self) -> Optional[List[str]]:
        """Detect the test command for the project.

        Returns:
            Test command list, or None if not detected.
        """
        # Check package.json
        package_json = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json):
            try:
                import json
                with open(package_json, "r") as f:
                    data = json.load(f)

                scripts = data.get("scripts", {})
                if "test" in scripts:
                    return ["npm", "run", "test"]

            except (json.JSONDecodeError, IOError):
                pass

        # Check for test files
        test_patterns = ["*.test.js", "*.spec.js", "test_*.py", "*_test.py"]
        for pattern in test_patterns:
            import glob
            if glob.glob(os.path.join(self.project_path, "**", pattern), recursive=True):
                break

        # Default to common commands
        for name, cmd in self.test_commands.items():
            try:
                import shutil
                if shutil.which(cmd[0]):
                    return cmd
            except (ImportError, TypeError):
                pass

        return None

    def run_tests(
        self,
        command: Optional[List[str]] = None,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> TestResult:
        """Run tests for the project.

        Args:
            command: Optional test command. If not provided, auto-detects.
            dry_run: If True, only show what would be run.
            verbose: If True, print output in real-time.

        Returns:
            TestResult with execution results.
        """
        import time

        start_time = time.time()

        # Detect command if not provided
        if command is None:
            command = self.detect_test_command()
            if command is None:
                return TestResult(
                    passed=False,
                    total=0,
                    failures=0,
                    errors=1,
                    duration=time.time() - start_time,
                    output="No test command detected",
                )

        # Dry-run mode
        if dry_run:
            output = f"Would run: {' '.join(command)}"
            return TestResult(
                passed=True,
                total=0,
                failures=0,
                errors=0,
                duration=time.time() - start_time,
                output=output,
            )

        # Run tests
        try:
            import subprocess

            # Set up process
            env = os.environ.copy()
            env["CI"] = "true"  # Run in CI mode for consistent output

            if verbose:
                # Print output in real-time
                process = subprocess.Popen(
                    command,
                    cwd=self.project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env,
                )

                output_lines = []
                for line in process.stdout:
                    print(line, end="")
                    output_lines.append(line)

                process.wait()
                output = "".join(output_lines)
                return_code = process.returncode

            else:
                # Capture output
                result = subprocess.run(
                    command,
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    env=env,
                )

                output = result.stdout + result.stderr
                return_code = result.returncode

            # Parse results
            passed = return_code == 0
            failures = 0
            errors = 0

            if not passed:
                # Try to count failures from output
                if "failed" in output.lower():
                    import re
                    matches = re.findall(r"(\d+)\s+(?:fail|error)", output.lower())
                    if matches:
                        failures = int(matches[0])

            return TestResult(
                passed=passed,
                total=0,  # Would need more sophisticated parsing
                failures=failures,
                errors=errors,
                duration=time.time() - start_time,
                output=output,
            )

        except Exception as e:
            return TestResult(
                passed=False,
                total=0,
                failures=0,
                errors=1,
                duration=time.time() - start_time,
                output=f"Error running tests: {e}",
            )

    def check_requirements(self) -> Dict[str, bool]:
        """Check if test requirements are met.

        Returns:
            Dictionary of requirement checks.
        """
        checks = {
            "project_exists": os.path.exists(self.project_path),
            "has_tests": False,
            "has_package_json": False,
            "has_pyproject": False,
        }

        # Check for test files
        import glob
        test_files = glob.glob(
            os.path.join(self.project_path, "**", "*.test.*"),
            recursive=True,
        )
        checks["has_tests"] = len(test_files) > 0

        # Check for config files
        checks["has_package_json"] = os.path.exists(
            os.path.join(self.project_path, "package.json")
        )
        checks["has_pyproject"] = os.path.exists(
            os.path.join(self.project_path, "pyproject.toml")
        )

        return checks


@contextmanager
def temporary_directory(suffix: str = "", prefix: str = "programisto_"):
    """Context manager for temporary directories.

    Args:
        suffix: Suffix for the directory name.
        prefix: Prefix for the directory name.

    Yields:
        Path to the temporary directory.
    """
    dirpath = tempfile.mkdtemp(suffix=suffix, prefix=prefix)
    try:
        yield dirpath
    finally:
        shutil.rmtree(dirpath, ignore_errors=True)
