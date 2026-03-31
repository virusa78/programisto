"""Log analyzer for Programisto.

Requirement 8: Log Analyzer

Scans and interprets log files to understand project state.
Categorizes logs by type (error, warning, info).
"""

import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import Counter

from scanner.project_scanner import ProjectStructure, FileAnalysis


class LogLevel(Enum):
    """Log severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    UNKNOWN = "unknown"


@dataclass
class LogEntry:
    """A single log entry."""

    content: str
    level: LogLevel
    timestamp: Optional[str] = None
    source: Optional[str] = None
    line_number: int = 0
    file_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "level": self.level.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "line_number": self.line_number,
            "file_path": self.file_path,
        }


@dataclass
class LogAnalysis:
    """Analysis of log files."""

    file_path: str
    entries: List[LogEntry] = field(default_factory=list)
    total_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    debug_count: int = 0
    unique_errors: List[str] = field(default_factory=list)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    time_range: Optional[tuple] = None
    first_entry: Optional[datetime] = None
    last_entry: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "total_count": self.total_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "debug_count": self.debug_count,
            "unique_errors": self.unique_errors[:10],  # Limit to first 10
            "error_patterns": self.error_patterns,
            "time_range": str(self.time_range) if self.time_range else None,
        }


class LogAnalyzer:
    """Analyzes log files in a project."""

    # Log level patterns
    LEVEL_PATTERNS = {
        LogLevel.ERROR: [
            r"\b(error|err|failed|failure|exception|fatal)\b",
            r"\[ERROR\]",
            r"\[error\]",
            r"ERROR:",
            r"error:",
            r"Exception:",
            r"Traceback",
            r"stack trace",
        ],
        LogLevel.WARNING: [
            r"\b(warning|warn|deprecated)\b",
            r"\[WARNING\]",
            r"\[WARN\]",
            r"\[warning\]",
            r"\[warn\]",
            r"WARNING:",
            r"warning:",
        ],
        LogLevel.INFO: [
            r"\b(info|information)\b",
            r"\[INFO\]",
            r"\[info\]",
            r"INFO:",
            r"info:",
            r"Starting",
            r"Started",
            r"Finished",
            r"Complete",
        ],
        LogLevel.DEBUG: [
            r"\b(debug|trace)\b",
            r"\[DEBUG\]",
            r"\[debug\]",
            r"DEBUG:",
            r"debug:",
            r"TRACE:",
        ],
    }

    # Timestamp patterns
    TIMESTAMP_PATTERNS = [
        r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)",
        r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})",
        r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})",
        r"(\d{2}:\d{2}:\d{2}\.\d+)",
    ]

    # Source patterns
    SOURCE_PATTERNS = [
        r"\[([a-zA-Z0-9_-]+)\]",
        r"(\w+\.js:\d+:\d+)",
        r"(\w+\.\w+:\d+)",
    ]

    def __init__(self, project_structure: Optional[ProjectStructure] = None):
        """Initialize the log analyzer.

        Args:
            project_structure: Optional project structure for context.
        """
        self.project_structure = project_structure
        self.analyses: Dict[str, LogAnalysis] = {}

    def analyze_project_logs(
        self, project_structure: Optional[ProjectStructure] = None
    ) -> Dict[str, LogAnalysis]:
        """Analyze all log files in a project.

        Args:
            project_structure: Project structure to analyze.

        Returns:
            Dictionary mapping file paths to their analysis.
        """
        if project_structure:
            self.project_structure = project_structure

        if not self.project_structure:
            return {}

        # Get log files from project structure
        log_files = self.project_structure.log_files

        if not log_files:
            # Try to find log files by scanning
            log_files = self._find_log_files()

        # Analyze each log file
        for log_file in log_files:
            analysis = self.analyze_file(log_file.path)
            if analysis:
                self.analyses[log_file.path] = analysis

        return self.analyses

    def _find_log_files(self) -> List[FileAnalysis]:
        """Find log files in the project directory."""
        if not self.project_structure:
            return []

        log_files: List[FileAnalysis] = []
        scan_dir = self.project_structure.root_path

        for root, dirs, files in os.walk(scan_dir):
            # Skip common non-log directories
            dirs[:] = [d for d in dirs if d not in {
                "node_modules",
                "__pycache__",
                ".git",
                ".cache",
            }]

            for filename in files:
                # Check if it's a log file
                if filename.endswith((".log", ".logs")):
                    filepath = os.path.join(root, filename)
                    try:
                        size = os.path.getsize(filepath)
                        # Skip very large files
                        if size > 10 * 1024 * 1024:  # 10MB
                            continue

                        rel_path = os.path.relpath(filepath, scan_dir)
                        log_files.append(FileAnalysis(
                            path=rel_path,
                            size=size,
                            extension=".log",
                            language="log",
                            is_log=True,
                        ))
                    except OSError:
                        continue

        return log_files

    def analyze_file(self, file_path: str) -> Optional[LogAnalysis]:
        """Analyze a single log file.

        Args:
            file_path: Path to the log file.

        Returns:
            LogAnalysis for the file.
        """
        try:
            # Build full path
            if self.project_structure:
                full_path = os.path.join(
                    self.project_structure.root_path,
                    file_path,
                )
            else:
                full_path = file_path

            if not os.path.exists(full_path):
                return None

            analysis = LogAnalysis(file_path=file_path)

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    entry = self._parse_log_entry(line, file_path, line_num)
                    if entry:
                        analysis.entries.append(entry)
                        analysis.total_count += 1

                        # Count by level
                        if entry.level == LogLevel.ERROR:
                            analysis.error_count += 1
                            self._track_error(analysis, entry)
                        elif entry.level == LogLevel.WARNING:
                            analysis.warning_count += 1
                        elif entry.level == LogLevel.INFO:
                            analysis.info_count += 1
                        elif entry.level == LogLevel.DEBUG:
                            analysis.debug_count += 1

                        # Track timestamps
                        if entry.timestamp:
                            try:
                                ts = self._parse_timestamp(entry.timestamp)
                                if analysis.first_entry is None or ts < analysis.first_entry:
                                    analysis.first_entry = ts
                                if analysis.last_entry is None or ts > analysis.last_entry:
                                    analysis.last_entry = ts
                                analysis.time_range = (
                                    analysis.first_entry,
                                    analysis.last_entry,
                                )
                            except (ValueError, TypeError):
                                pass

            return analysis

        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return None

    def _parse_log_entry(self, line: str, file_path: str, line_num: int) -> Optional[LogEntry]:
        """Parse a single log line.

        Args:
            line: The log line to parse.
            file_path: Source file path.
            line_num: Line number.

        Returns:
            LogEntry if parsing succeeds, None otherwise.
        """
        # Determine log level
        level = self._detect_level(line)

        # Extract timestamp
        timestamp = self._extract_timestamp(line)

        # Extract source
        source = self._extract_source(line)

        return LogEntry(
            content=line,
            level=level,
            timestamp=timestamp,
            source=source,
            line_number=line_num,
            file_path=file_path,
        )

    def _detect_level(self, line: str) -> LogLevel:
        """Detect the log level from a line."""
        line_lower = line.lower()

        # Check error patterns first (they're most specific)
        for pattern in self.LEVEL_PATTERNS[LogLevel.ERROR]:
            if re.search(pattern, line_lower, re.IGNORECASE):
                return LogLevel.ERROR

        # Check warning patterns
        for pattern in self.LEVEL_PATTERNS[LogLevel.WARNING]:
            if re.search(pattern, line_lower, re.IGNORECASE):
                return LogLevel.WARNING

        # Check info patterns
        for pattern in self.LEVEL_PATTERNS[LogLevel.INFO]:
            if re.search(pattern, line_lower, re.IGNORECASE):
                return LogLevel.INFO

        # Check debug patterns
        for pattern in self.LEVEL_PATTERNS[LogLevel.DEBUG]:
            if re.search(pattern, line_lower, re.IGNORECASE):
                return LogLevel.DEBUG

        return LogLevel.UNKNOWN

    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from a log line."""
        for pattern in self.TIMESTAMP_PATTERNS:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None

    def _extract_source(self, line: str) -> Optional[str]:
        """Extract source/component from a log line."""
        for pattern in self.SOURCE_PATTERNS:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse a timestamp string."""
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%b %d %H:%M:%S",
            "%H:%M:%S.%f",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        return None

    def _track_error(self, analysis: LogAnalysis, entry: LogEntry) -> None:
        """Track error for pattern analysis."""
        # Extract error message (without timestamp and level)
        error_msg = re.sub(r"\[\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}.*?\]", "", entry.content)
        error_msg = re.sub(r"\b(ERROR|WARN|INFO|DEBUG):\s*", "", error_msg, flags=re.IGNORECASE)
        error_msg = error_msg.strip()

        # Add to unique errors if not already present
        if error_msg and error_msg not in analysis.unique_errors:
            analysis.unique_errors.append(error_msg)

        # Track error patterns
        pattern = self._simplify_error(error_msg)
        if pattern:
            analysis.error_patterns[pattern] = analysis.error_patterns.get(pattern, 0) + 1

    def _simplify_error(self, error_msg: str) -> Optional[str]:
        """Simplify an error message to a pattern."""
        # Remove specific values
        simplified = re.sub(r"\b\d+\b", "<NUM>", error_msg)
        simplified = re.sub(r"[a-f0-9]{8,}", "<UUID>", simplified, flags=re.IGNORECASE)
        simplified = re.sub(r'["\'][^"\']+["\']', "<STRING>", simplified)
        simplified = re.sub(r"/[^/\s]+/", "<PATH>", simplified)

        return simplified[:200] if simplified else None

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all log analyses.

        Returns:
            Summary dictionary.
        """
        if not self.analyses:
            return {
                "total_files": 0,
                "total_entries": 0,
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "files": [],
            }

        total_entries = sum(a.total_count for a in self.analyses.values())
        total_errors = sum(a.error_count for a in self.analyses.values())
        total_warnings = sum(a.warning_count for a in self.analyses.values())
        total_info = sum(a.info_count for a in self.analyses.values())

        return {
            "total_files": len(self.analyses),
            "total_entries": total_entries,
            "error_count": total_errors,
            "warning_count": total_warnings,
            "info_count": total_info,
            "files": [a.file_path for a in self.analyses.values()],
        }

    def get_errors(self) -> List[Dict[str, Any]]:
        """Get all error entries.

        Returns:
            List of error entries.
        """
        errors = []
        for analysis in self.analyses.values():
            for entry in analysis.entries:
                if entry.level == LogLevel.ERROR:
                    errors.append(entry.to_dict())
        return errors

    def get_warnings(self) -> List[Dict[str, Any]]:
        """Get all warning entries.

        Returns:
            List of warning entries.
        """
        warnings = []
        for analysis in self.analyses.values():
            for entry in analysis.entries:
                if entry.level == LogLevel.WARNING:
                    warnings.append(entry.to_dict())
        return warnings

    def generate_report(self) -> str:
        """Generate a human-readable log analysis report.

        Returns:
            Report string.
        """
        if not self.analyses:
            return "No log files found to analyze."

        summary = self.get_summary()

        lines = [
            "## Log Analysis Report",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "### Summary",
            f"- **Files analyzed**: {summary['total_files']}",
            f"- **Total entries**: {summary['total_entries']}",
            f"- **Errors**: {summary['error_count']}",
            f"- **Warnings**: {summary['warning_count']}",
            f"- **Info messages**: {summary['info_count']}",
            "",
        ]

        # Add file-by-file breakdown
        lines.append("### Files")
        for file_path, analysis in self.analyses.items():
            lines.extend([
                f"#### {file_path}",
                f"- Entries: {analysis.total_count}",
                f"- Errors: {analysis.error_count}",
                f"- Warnings: {analysis.warning_count}",
                "",
            ])

            # Show unique errors if any
            if analysis.unique_errors:
                lines.append("**Unique Errors:**")
                for error in analysis.unique_errors[:5]:  # Limit to 5
                    lines.append(f"- {error[:100]}...")
                lines.append("")

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all analyses."""
        self.analyses.clear()


# Global analyzer instance
_analyzer: Optional[LogAnalyzer] = None


def get_analyzer(
    project_structure: Optional[ProjectStructure] = None,
) -> LogAnalyzer:
    """Get or create the global log analyzer."""
    global _analyzer

    if _analyzer is None:
        _analyzer = LogAnalyzer(project_structure)

    return _analyzer
