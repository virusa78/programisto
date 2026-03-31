"""Main assistant functionality for Programisto.

Requirement 3: Main Assistant Functionality

Provides a command-line interface for interacting with the assistant.
Maintains conversation context across interactions.
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from llm.client import LLMClient, ChatMessage, ChatRole, LLMResponse
from scanner.project_scanner import ProjectScanner, ProjectStructure
from context.prompts import ContextPromptBuilder, ContextData

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """State for the conversation."""

    messages: List[ChatMessage] = field(default_factory=list)
    context: ContextData = field(default_factory=ContextData)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.messages.append(ChatMessage(ChatRole.USER, content))
        self.last_updated = datetime.now().isoformat()

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self.messages.append(ChatMessage(ChatRole.ASSISTANT, content))
        self.last_updated = datetime.now().isoformat()

    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self.messages.append(ChatMessage(ChatRole.SYSTEM, content))


class ProgramistoAssistant:
    """The main Programisto assistant."""

    # Command handlers
    COMMANDS = {
        "help": "Show available commands",
        "scan": "Rescan the project directory",
        "context": "Show current context",
        "clear": "Clear conversation history",
        "quit": "Exit the assistant",
        "exit": "Exit the assistant",
        "foil": "Generate code foils/patterns",
        "harness": "Generate engineering harness",
        "log": "Analyze log files",
        "skills": "Show available skills",
        "skill-select": "Select skills for the project",
        "admin": "Admin commands",
    }

    def __init__(
        self,
        project_path: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        verbose: bool = False,
    ):
        """Initialize the assistant.

        Args:
            project_path: Path to the project directory.
            llm_client: Optional LLM client instance.
            verbose: Enable verbose output.
        """
        self.project_path = project_path or os.getcwd()
        self.llm_client = llm_client
        self.verbose = verbose
        self.scanner = ProjectScanner()
        self.prompt_builder = ContextPromptBuilder()
        self.state = ConversationState()

        # Initialize LLM client if not provided
        if not self.llm_client:
            from config import get_config

            config = get_config()
            self.llm_client = LLMClient(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url,
                model=config.llm.model,
            )

        # Initial scan
        self.project_structure = self._scan_project()

        # Set up system message
        self._initialize_system_message()

    def _initialize_system_message(self) -> None:
        """Set up the system message for the conversation."""
        system_prompt = self._build_system_prompt()
        self.state.add_system_message(system_prompt)

    def _build_system_prompt(self) -> str:
        """Build the system prompt based on project context."""
        parts = [
            "You are Programisto, a focused coding assistant for web developers.",
            "",
            "Your role is to:",
            "- Help developers build and maintain web projects",
            "- Provide context-aware coding assistance",
            "- Generate appropriate code patterns and templates",
            "- Follow engineering best practices",
            "- Stay within the project's scope",
            "",
            "Key principles:",
            "- Only suggest changes within the project directory",
            "- Adapt your responses to the project's technology stack",
            "- If TypeScript is detected, use TypeScript patterns",
            "- Provide complete, working code examples",
            "- Explain your reasoning when appropriate",
            "",
        ]

        # Add context info
        if self.project_structure:
            tech_stack = self.project_structure.technology_stack
            if tech_stack.get("typescript"):
                parts.append(
                    "The project uses TypeScript. Use strict typing, "
                    "interfaces for public APIs, and type inference where appropriate."
                )
                parts.append("")

            if tech_stack.get("react"):
                parts.append(
                    "The project uses React. Use functional components, "
                    "hooks for state management, and follow React best practices."
                )
                parts.append("")

        return "\n".join(parts)

    def _scan_project(self) -> Optional[ProjectStructure]:
        """Scan the project directory."""
        try:
            structure = self.scanner.scan(self.project_path)
            self.prompt_builder.build_context(structure)
            return structure
        except Exception as e:
            logger.warning(f"Failed to scan project: {e}")
            return None

    def process_command(self, command: str) -> str:
        """Process a user command.

        Args:
            command: The command string.

        Returns:
            Response from the assistant.
        """
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Handle built-in commands
        if cmd in self.COMMANDS:
            return self._handle_command(cmd, args)

        # Default: treat as a question for the LLM
        return self._answer_question(command)

    def _handle_command(self, cmd: str, args: str) -> str:
        """Handle a built-in command."""
        handlers = {
            "help": lambda: self._cmd_help(),
            "scan": lambda: self._cmd_scan(),
            "context": lambda: self._cmd_context(),
            "clear": lambda: self._cmd_clear(),
            "quit": lambda: self._cmd_quit(),
            "exit": lambda: self._cmd_exit(),
            "foil": lambda: self._cmd_foil(args),
            "harness": lambda: self._cmd_harness(args),
            "log": lambda: self._cmd_log(),
            "skills": lambda: self._cmd_skills(),
            "skill-select": lambda: self._cmd_skill_select(args),
            "admin": lambda: self._cmd_admin(args),
        }

        handler = handlers.get(cmd)
        if handler:
            try:
                return handler()
            except Exception as e:
                return f"Error: {e}"
        return f"Unknown command: {cmd}"

    def _cmd_help(self) -> str:
        """Show help for available commands."""
        lines = ["Available Commands:", ""]
        for cmd, desc in sorted(self.COMMANDS.items()):
            lines.append(f"  {cmd:15} {desc}")
        lines.append("")
        lines.append("Type a question or command to get started.")
        return "\n".join(lines)

    def _cmd_scan(self) -> str:
        """Rescan the project directory."""
        self.project_structure = self._scan_project()
        if self.project_structure:
            lines = [
                f"Scanned {self.project_structure.file_count} files",
                f"Technology stack: {', '.join(self.project_structure.technology_stack.keys()) or 'none'}",
            ]
            return "\n".join(lines)
        return "Failed to scan project directory"

    def _cmd_context(self) -> str:
        """Show current context."""
        context = self.prompt_builder.build_context(self.project_structure)
        lines = [
            "Current Context:",
            f"Project: {context.project_name}",
            f"Files: {len(context.project_files)}",
            f"Technologies: {', '.join(k for k, v in context.technology_stack.items() if v) or 'none'}",
            "",
            "Conversation History:",
            f"Messages: {len(self.state.messages)}",
        ]
        return "\n".join(lines)

    def _cmd_clear(self) -> str:
        """Clear conversation history."""
        # Keep system message, clear others
        self.state.messages = [self.state.messages[0]] if self.state.messages else []
        return "Conversation history cleared."

    def _cmd_quit(self) -> str:
        """Exit the assistant."""
        return "Goodbye!"

    def _cmd_exit(self) -> str:
        """Exit the assistant."""
        return "Goodbye!"

    def _answer_question(self, question: str) -> str:
        """Answer a question using the LLM.

        Args:
            question: The user's question.

        Returns:
            The LLM's response.
        """
        # Add user message to context
        self.state.add_user_message(question)

        # Build context-aware prompt
        prompt = self.prompt_builder.build_prompt(
            question,
            include_file_content=True,
            max_file_content=3,
        )

        # Prepare messages for LLM
        messages = list(self.state.messages)
        messages.append(ChatMessage(ChatRole.USER, prompt))

        # Call LLM with loading indicator
        print("Thinking...", flush=True)

        try:
            response = self.llm_client.chat(messages)
            self.state.add_assistant_message(response.content)
            return response.content

        except Exception as e:
            return f"Error: Failed to get response from LLM: {e}"

    def interactive_mode(self) -> None:
        """Run the assistant in interactive mode."""
        print("Programisto - Your coding companion")
        print("Type 'help' for available commands, or ask a question.")
        print()

        try:
            while True:
                try:
                    command = input("\n> ").strip()
                except EOFError:
                    print("\nGoodbye!")
                    break

                if not command:
                    continue

                if command.lower() in ("quit", "exit"):
                    response = self._cmd_exit()
                    print(response)
                    break

                response = self.process_command(command)
                print(response)

        except KeyboardInterrupt:
            print("\nGoodbye!")

    def run(self, query: Optional[str] = None) -> str:
        """Run the assistant with a single query or interactive mode.

        Args:
            query: Optional single query to answer.

        Returns:
            The response text.
        """
        if query:
            return self.process_command(query)

        self.interactive_mode()
        return ""


# Main entry point
def main():
    """Main entry point for the assistant."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Programisto - Your coding companion"
    )
    parser.add_argument(
        "--project",
        "-p",
        help="Path to project directory",
        default=None,
    )
    parser.add_argument(
        "--query",
        "-q",
        help="Single query to answer",
        default=None,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run assistant
    assistant = ProgramistoAssistant(
        project_path=args.project, verbose=args.verbose
    )

    if args.query:
        print(assistant.run(args.query))
    else:
        assistant.run()


if __name__ == "__main__":
    main()
