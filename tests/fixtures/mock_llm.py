"""Mock LLM client for testing."""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from llm.client import ChatMessage, ChatRole, LLMResponse


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, response: str = "Mock response"):
        """Initialize with optional response.

        Args:
            response: Default response to return.
        """
        self.response = response
        self.call_count = 0
        self.last_messages: List[List[ChatMessage]] = []
        self.response_callback: Optional[Callable[[List[ChatMessage]], str]] = None

    def set_response(self, response: str) -> None:
        """Set the mock response."""
        self.response = response

    def set_callback(self, callback: Callable[[List[ChatMessage]], str]) -> None:
        """Set a callback to generate responses dynamically."""
        self.response_callback = callback

    def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Simulate an LLM chat.

        Args:
            messages: Chat messages.
            temperature: Temperature (ignored).
            max_tokens: Max tokens (ignored).
            stop: Stop sequences (ignored).

        Returns:
            Mock LLM response.
        """
        self.call_count += 1
        self.last_messages.append(messages)

        if self.response_callback:
            content = self.response_callback(messages)
        else:
            content = self.response

        return LLMResponse(
            content=content,
            model="mock-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Simulate text generation.

        Args:
            prompt: Input prompt.
            system_message: System message (ignored).
            temperature: Temperature (ignored).
            max_tokens: Max tokens (ignored).

        Returns:
            Mock LLM response.
        """
        messages = [ChatMessage(ChatRole.SYSTEM, system_message or "")] if system_message else []
        messages.append(ChatMessage(ChatRole.USER, prompt))
        return self.chat(messages, temperature, max_tokens)

    def get_call_count(self) -> int:
        """Get the number of times chat was called."""
        return self.call_count

    def reset(self) -> None:
        """Reset call count and history."""
        self.call_count = 0
        self.last_messages = []


# Fixture for pytest
def mock_llm_client(response: str = "Test response") -> MockLLMClient:
    """Create a mock LLM client.

    Args:
        response: Default response.

    Returns:
        MockLLMClient instance.
    """
    return MockLLMClient(response)


def mock_llm_callback(
    expected_query: str,
    response: str,
) -> Callable[[List[ChatMessage]], str]:
    """Create a callback that responds to specific queries.

    Args:
        expected_query: Query to match.
        response: Response to return.

    Returns:
        Callback function.
    """
    def callback(messages: List[ChatMessage]) -> str:
        # Find the user message
        for msg in messages:
            if msg.role == ChatRole.USER and expected_query in msg.content:
                return response
        return "Default response"

    return callback
