#!/usr/bin/env python3
"""Programisto - Your coding companion.

A Python-based assistant for young vibe developers.
"""

import os
import sys
import argparse
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config, ProgramistoConfig, save_config
from scanner.project_scanner import ProjectScanner
from llm.client import LLMClient
from assistant.main import ProgramistoAssistant
from foils.generator import FoilGenerator, get_generator as get_foil_generator
from harness.generator import HarnessGenerator, get_generator as get_harness_generator
from analyzer.log_analyzer import LogAnalyzer, get_analyzer
from skills.catalog import SkillCatalog, get_catalog
from skills.selector import SkillSelector, get_selector
from tools.cli_support import CLISupport, get_cli_support
from admin.commands import AdminCommands, get_admin
from utils.testing import DryRunExecutor


# Configure logging
def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=level, format=format_str)


def cmd_help(args: argparse.Namespace) -> int:
    """Show help message."""
    print("""Programisto - Your coding companion

Usage: programisto [command] [options]

Commands:
  help          Show this help message
  scan          Scan the project directory
  chat          Start interactive assistant mode
  foil          Generate code foils/patterns
  harness       Generate engineering harness tools
  log           Analyze log files
  skills        Manage skills
  tools         Manage CLI tool configurations
  admin         Run admin commands
  validate      Validate project setup

Options:
  -p, --project PATH   Path to project directory (default: current directory)
  -q, --query TEXT     Single query to answer
  -v, --verbose        Enable verbose output
  -n, --dry-run        Enable dry-run mode
  --config PATH        Path to configuration file

Examples:
  programisto help
  programisto scan
  programisto chat
  programisto --query "How do I add a new component?"
  programisto foil --output ./src/components
  programisto admin new-project my-project
""")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    """Scan the project directory."""
    scanner = ProjectScanner()

    project_path = args.project or os.getcwd()

    print(f"Scanning: {project_path}")
    structure = scanner.scan(project_path)

    print(f"\nScan complete!")
    print(f"  Files: {structure.file_count}")
    print(f"  Size: {structure.total_size / 1024:.1f} KB")
    print(f"  Technologies: {', '.join(structure.technology_stack.keys()) or 'none'}")

    if structure.log_files:
        print(f"  Log files: {len(structure.log_files)}")

    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    """Start interactive chat mode."""
    setup_logging(args.verbose)

    # Set up dry-run if requested
    if args.dry_run:
        DryRunExecutor(enabled=True)

    project_path = args.project or os.getcwd()

    # Initialize LLM client
    config = get_config()
    llm_client = LLMClient(
        api_key=config.llm.api_key,
        base_url=config.llm.base_url,
        model=config.llm.model,
    )

    # Create and run assistant
    assistant = ProgramistoAssistant(
        project_path=project_path,
        llm_client=llm_client,
        verbose=args.verbose,
    )

    if args.query:
        print(assistant.run(args.query))
    else:
        assistant.run()

    return 0


def cmd_foil(args: argparse.Namespace) -> int:
    """Generate code foils."""
    project_path = args.project or os.getcwd()

    # Scan project first
    scanner = ProjectScanner()
    structure = scanner.scan(project_path)

    # Generate foils
    generator = FoilGenerator(structure)
    foils = generator.generate_foils()

    if args.output:
        # Save to files
        saved = generator.save_foils(foils, args.output)
        print(f"Saved {len(saved)} foil files to {args.output}")
        for path in saved:
            print(f"  {path}")
    else:
        # Print to stdout
        print(generator.get_foils_as_code(foils))

    return 0


def cmd_harness(args: argparse.Namespace) -> int:
    """Generate engineering harness."""
    project_path = args.project or os.getcwd()

    # Scan project first
    scanner = ProjectScanner()
    structure = scanner.scan(project_path)

    # Generate harness
    generator = HarnessGenerator(structure)
    tools = generator.generate_harness()

    if args.output:
        # Save to files
        saved = generator.save_harness(args.output)
        print(f"Saved {len(saved)} harness files to {args.output}")
    else:
        # Print summary
        print(f"Generated {len(tools)} tools")
        print("\nBest practices:")
        for practice in generator.get_best_practices()[:5]:
            print(f"  - {practice}")

    return 0


def cmd_log(args: argparse.Namespace) -> int:
    """Analyze log files."""
    project_path = args.project or os.getcwd()

    # Scan project first
    scanner = ProjectScanner()
    structure = scanner.scan(project_path)

    # Analyze logs
    analyzer = LogAnalyzer(structure)
    analyses = analyzer.analyze_project_logs()

    if not analyses:
        print("No log files found.")
        return 0

    # Print report
    print(analyzer.generate_report())

    return 0


def cmd_skills(args: argparse.Namespace) -> int:
    """Manage skills."""
    catalog = get_catalog()
    catalog.ensure_index()

    if args.action == "list":
        # List all skills
        print("Available Skills")
        print("================")
        for skill_id, metadata in catalog.index.skills.items():
            print(f"\n{metadata.name} ({skill_id})")
            print(f"  Category: {metadata.category}")
            print(f"  Description: {metadata.description[:80]}...")
            print(f"  Tags: {', '.join(metadata.tags)}")
            print(f"  Priority: {metadata.priority}")

    elif args.action == "search":
        # Search skills
        results = catalog.search_skills(args.query)
        print(f"Found {len(results)} skills matching '{args.query}'")
        for skill in results:
            print(f"  - {skill.name} ({skill.id})")

    elif args.action == "categories":
        # List categories
        categories = catalog.get_categories()
        print("Categories:")
        for cat in categories:
            print(f"  - {cat}")

    elif args.action == "tags":
        # List tags
        tags = catalog.get_tags()
        print("Tags:")
        for tag in tags:
            print(f"  - {tag}")

    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    """Manage CLI tool configurations."""
    cli_support = get_cli_support()

    if args.action == "list":
        # List configured tools
        print("Configured CLI Tools")
        print("===================")
        for tool_name in cli_support.DEFAULT_TOOLS:
            config = cli_support.get_tool_config(tool_name.replace("_", "-"))
            if config:
                status = "enabled" if config.get("enabled", True) else "disabled"
                print(f"  {tool_name}: {status}")

    elif args.action == "enable":
        # Enable a tool
        if cli_support.add_tool(args.tool_name):
            cli_support.save_config()
            print(f"Enabled tool: {args.tool_name}")
        else:
            print(f"Unknown tool: {args.tool_name}")
            return 1

    elif args.action == "disable":
        # Disable a tool
        if cli_support.remove_tool(args.tool_name):
            cli_support.save_config()
            print(f"Disabled tool: {args.tool_name}")
        else:
            print(f"Unknown tool: {args.tool_name}")
            return 1

    elif args.action == "validate":
        # Validate configuration
        errors = cli_support.validate_config()
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print("Configuration is valid.")

    return 0


def cmd_admin(args: argparse.Namespace) -> int:
    """Run admin commands."""
    config = get_config()
    admin = get_admin(config)

    if args.subcommand == "add-skill-repo":
        # Add a skill repository
        result = admin.add_skill_repo(args.url, args.name)
        print(result.message)
        return 0 if result.success else 1

    elif args.subcommand == "add-cli":
        # Add a CLI tool
        result = admin.add_cli(args.cli_name)
        print(result.message)
        if result.data and "instructions" in result.data:
            print(result.data["instructions"])
        return 0 if result.success else 1

    elif args.subcommand == "new-project":
        # Create a new project
        result = admin.new_project(args.project_name, args.template)
        print(result.message)
        return 0 if result.success else 1

    elif args.subcommand == "list-skills":
        # List skills
        result = admin.list_skills()
        print(result.message)
        for skill in result.data.get("skills", []):
            print(f"  - {skill['name']} ({skill['id']})")

    elif args.subcommand == "list-tools":
        # List tools
        result = admin.list_tools()
        print(result.message)
        for tool in result.data.get("tools", []):
            status = "enabled" if tool.get("enabled") else "disabled"
            print(f"  - {tool['name']}: {status}")

    elif args.subcommand == "validate":
        # Validate project
        result = admin.validate_project(args.project_path)
        print(result.message)
        if result.data.get("issues"):
            print("\nIssues:")
            for issue in result.data["issues"]:
                print(f"  - {issue}")
        if result.data.get("warnings"):
            print("\nWarnings:")
            for warning in result.data["warnings"]:
                print(f"  - {warning}")
        return 0 if result.success else 1

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate project setup."""
    project_path = args.project or os.getcwd()

    # Check basic requirements
    checks = {
        "project_exists": os.path.exists(project_path),
        "has_config": os.path.exists(os.path.join(project_path, "programisto-config.yaml")),
        "has_skills_catalog": os.path.exists(os.path.join(project_path, "skills_catalog")),
        "has_context": os.path.exists(os.path.join(project_path, "PROJECT_CONTEXT.md")),
    }

    print("Project Validation")
    print("==================")
    for check, passed in checks.items():
        status = "OK" if passed else "MISSING"
        print(f"  {check}: {status}")

    # Validate CLI config
    cli_support = get_cli_support()
    errors = cli_support.validate_config()
    if errors:
        print("\nConfiguration Issues:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nValidation passed!")
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Programisto - Your coding companion",
        prog="programisto",
    )

    parser.add_argument(
        "-p", "--project",
        help="Path to project directory",
        default=None,
    )
    parser.add_argument(
        "-q", "--query",
        help="Single query to answer",
        default=None,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Enable dry-run mode",
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default=None,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Help command
    subparsers.add_parser("help", help="Show help message")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan project directory")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive mode")

    # Foil command
    foil_parser = subparsers.add_parser("foil", help="Generate code foils")
    foil_parser.add_argument(
        "-o", "--output",
        help="Output directory for foils",
        default=None,
    )

    # Harness command
    harness_parser = subparsers.add_parser("harness", help="Generate engineering harness")
    harness_parser.add_argument(
        "-o", "--output",
        help="Output directory for harness files",
        default=None,
    )

    # Log command
    log_parser = subparsers.add_parser("log", help="Analyze log files")

    # Skills command
    skills_parser = subparsers.add_parser("skills", help="Manage skills")
    skills_parser.add_argument(
        "action",
        choices=["list", "search", "categories", "tags"],
        nargs="?",
        default="list",
        help="Skills action",
    )
    skills_parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Search query",
    )

    # Tools command
    tools_parser = subparsers.add_parser("tools", help="Manage CLI tools")
    tools_parser.add_argument(
        "action",
        choices=["list", "enable", "disable", "validate"],
        nargs="?",
        default="list",
        help="Tools action",
    )
    tools_parser.add_argument(
        "tool_name",
        nargs="?",
        help="Tool name",
    )

    # Admin command
    admin_parser = subparsers.add_parser("admin", help="Admin commands")
    admin_subparsers = admin_parser.add_subparsers(dest="subcommand")

    # admin add-skill-repo
    add_repo_parser = admin_subparsers.add_parser(
        "add-skill-repo",
        help="Add a skill repository",
    )
    add_repo_parser.add_argument("url", help="Repository URL")
    add_repo_parser.add_argument(
        "-n", "--name",
        help="Repository name",
    )

    # admin add-cli
    add_cli_parser = admin_subparsers.add_parser(
        "add-cli",
        help="Add a CLI tool",
    )
    add_cli_parser.add_argument("cli_name", help="CLI tool name")

    # admin new-project
    new_project_parser = admin_subparsers.add_parser(
        "new-project",
        help="Create a new project",
    )
    new_project_parser.add_argument("project_name", help="Project name")
    new_project_parser.add_argument(
        "-t", "--template",
        help="Template to use",
    )

    # admin list-skills
    admin_subparsers.add_parser("list-skills", help="List available skills")

    # admin list-tools
    admin_subparsers.add_parser("list-tools", help="List configured tools")

    # admin validate
    validate_parser = admin_subparsers.add_parser(
        "validate",
        help="Validate project setup",
    )
    validate_parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project path to validate",
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate project setup",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Load configuration
    if args.config:
        config = ProgramistoConfig.load(args.config)
    else:
        config = get_config()

    if args.project:
        config.project_dir = args.project

    # Route to command handler
    if args.command == "help" or not args.command:
        return cmd_help(args)

    elif args.command == "scan":
        return cmd_scan(args)

    elif args.command == "chat":
        return cmd_chat(args)

    elif args.command == "foil":
        return cmd_foil(args)

    elif args.command == "harness":
        return cmd_harness(args)

    elif args.command == "log":
        return cmd_log(args)

    elif args.command == "skills":
        return cmd_skills(args)

    elif args.command == "tools":
        return cmd_tools(args)

    elif args.command == "admin":
        if not args.subcommand:
            print("Please specify an admin subcommand")
            return 1
        return cmd_admin(args)

    elif args.command == "validate":
        return cmd_validate(args)

    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
