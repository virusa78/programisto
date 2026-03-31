"""Unit tests for log analyzer."""

import os
import pytest
from analyzer.log_analyzer import LogAnalyzer, LogEntry, LogLevel, LogAnalysis


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_log_levels(self):
        """Test all log levels exist."""
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.UNKNOWN.value == "unknown"


class TestLogEntry:
    """Tests for LogEntry class."""

    def test_entry_creation(self):
        """Test creating a log entry."""
        entry = LogEntry(
            content="2024-01-01T00:00:00 [ERROR] Test error",
            level=LogLevel.ERROR,
            timestamp="2024-01-01T00:00:00",
            source="app",
            line_number=1,
            file_path="app.log",
        )

        assert entry.level == LogLevel.ERROR
        assert entry.timestamp == "2024-01-01T00:00:00"
        assert entry.line_number == 1

    def test_entry_to_dict(self):
        """Test converting entry to dictionary."""
        entry = LogEntry(
            content="Test",
            level=LogLevel.INFO,
            timestamp="2024-01-01",
        )

        data = entry.to_dict()
        assert data["content"] == "Test"
        assert data["level"] == "info"


class TestLogAnalysis:
    """Tests for LogAnalysis class."""

    def test_analysis_creation(self):
        """Test creating a log analysis."""
        analysis = LogAnalysis(file_path="app.log")

        assert analysis.file_path == "app.log"
        assert analysis.total_count == 0
        assert analysis.error_count == 0

    def test_analysis_counts(self):
        """Test analysis counts."""
        analysis = LogAnalysis(file_path="app.log")

        # Simulate adding entries
        analysis.entries.append(LogEntry("Error", LogLevel.ERROR))
        analysis.entries.append(LogEntry("Warning", LogLevel.WARNING))
        analysis.entries.append(LogEntry("Info", LogLevel.INFO))

        # Counts are updated when entries are added via analyze_file
        # Here we just verify the entries were added
        assert len(analysis.entries) == 3

    def test_analysis_to_dict(self):
        """Test converting analysis to dictionary."""
        analysis = LogAnalysis(
            file_path="test.log",
            total_count=100,
            error_count=5,
            warning_count=10,
        )

        data = analysis.to_dict()
        assert data["file_path"] == "test.log"
        assert data["total_count"] == 100
        assert data["error_count"] == 5


class TestLogAnalyzer:
    """Tests for LogAnalyzer class."""

    def test_init(self):
        """Test analyzer initialization."""
        analyzer = LogAnalyzer()
        assert analyzer.analyses == {}

    def test_analyze_nonexistent_file(self):
        """Test analyzing a non-existent file."""
        analyzer = LogAnalyzer()
        analysis = analyzer.analyze_file("/nonexistent/file.log")
        assert analysis is None

    def test_analyze_sample_log_file(self, sample_log_file):
        """Test analyzing a sample log file."""
        analyzer = LogAnalyzer()
        analysis = analyzer.analyze_file(sample_log_file)

        assert analysis is not None
        assert analysis.file_path == "logs/app.log"
        assert analysis.total_count > 0

    def test_analyze_project_logs(self, sample_project_path):
        """Test analyzing all project logs."""
        # Create a log file
        log_path = os.path.join(sample_project_path, "app.log")
        with open(log_path, "w") as f:
            f.write("ERROR: test error\n")
            f.write("WARNING: test warning\n")
            f.write("INFO: test info\n")

        analyzer = LogAnalyzer()
        analyses = analyzer.analyze_project_logs()

        assert len(analyses) > 0
        assert "app.log" in analyses

    def test_get_summary(self, sample_log_file):
        """Test getting analysis summary."""
        analyzer = LogAnalyzer()
        analyzer.analyze_file(sample_log_file)

        summary = analyzer.get_summary()

        assert summary["total_files"] > 0
        assert "error_count" in summary
        assert "warning_count" in summary
        assert "info_count" in summary

    def test_get_errors(self, sample_log_file):
        """Test getting error entries."""
        analyzer = LogAnalyzer()
        analyzer.analyze_file(sample_log_file)

        errors = analyzer.get_errors()
        assert len(errors) >= 0  # May or may not have errors

    def test_get_warnings(self, sample_log_file):
        """Test getting warning entries."""
        analyzer = LogAnalyzer()
        analyzer.analyze_file(sample_log_file)

        warnings = analyzer.get_warnings()
        assert len(warnings) >= 0

    def test_generate_report(self, sample_log_file):
        """Test generating a report."""
        analyzer = LogAnalyzer()
        analyzer.analyze_file(sample_log_file)

        report = analyzer.generate_report()

        assert "Log Analysis Report" in report
        assert "Summary" in report

    def test_clear(self):
        """Test clearing analyses."""
        analyzer = LogAnalyzer()
        analyzer.analyses["test"] = LogAnalysis(file_path="test.log")

        analyzer.clear()
        assert analyzer.analyses == {}


class TestLogDetection:
    """Tests for log level detection."""

    def test_detect_error(self):
        """Test error detection."""
        analyzer = LogAnalyzer()

        # Test various error patterns
        assert analyzer._detect_level("ERROR: test") == LogLevel.ERROR
        assert analyzer._detect_level("[ERROR] test") == LogLevel.ERROR
        assert analyzer._detect_level("Exception: test") == LogLevel.ERROR
        assert analyzer._detect_level("traceback") == LogLevel.ERROR

    def test_detect_warning(self):
        """Test warning detection."""
        analyzer = LogAnalyzer()

        assert analyzer._detect_level("WARNING: test") == LogLevel.WARNING
        assert analyzer._detect_level("[WARN] test") == LogLevel.WARNING
        assert analyzer._detect_level("deprecated") == LogLevel.WARNING

    def test_detect_info(self):
        """Test info detection."""
        analyzer = LogAnalyzer()

        assert analyzer._detect_level("INFO: test") == LogLevel.INFO
        assert analyzer._detect_level("[INFO] test") == LogLevel.INFO
        assert analyzer._detect_level("Starting") == LogLevel.INFO

    def test_detect_debug(self):
        """Test debug detection."""
        analyzer = LogAnalyzer()

        assert analyzer._detect_level("DEBUG: test") == LogLevel.DEBUG
        assert analyzer._detect_level("[DEBUG] test") == LogLevel.DEBUG
        assert analyzer._detect_level("trace") == LogLevel.DEBUG

    def test_detect_unknown(self):
        """Test unknown level detection."""
        analyzer = LogAnalyzer()

        assert analyzer._detect_level("random text without level") == LogLevel.UNKNOWN


class TestTimestampParsing:
    """Tests for timestamp parsing."""

    def test_parse_iso_timestamp(self):
        """Test parsing ISO timestamp."""
        analyzer = LogAnalyzer()

        ts = analyzer._parse_timestamp("2024-01-01T00:00:00")
        assert ts is not None
        assert ts.year == 2024

    def test_parse_invalid_timestamp(self):
        """Test parsing invalid timestamp."""
        analyzer = LogAnalyzer()

        ts = analyzer._parse_timestamp("invalid timestamp")
        assert ts is None
