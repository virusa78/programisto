"""External LLM client for Programisto.

Requirement 2: External LLM Integration

Connects to an OpenAI-compatible API endpoint for context-aware responses.
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Error from LLM API."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ChatRole(Enum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """A chat message."""

    role: ChatRole
    content: str
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {"role": self.role.value, "content": self.content}
        if self.name:
            data["name"] = self.name
        return data


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
        }


class LLMClient:
    """Client for OpenAI-compatible LLM APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "claude-3-sonnet-20240229",
        timeout: int = 120,
    ):
        """Initialize the LLM client.

        Args:
            api_key: API key for authentication. Defaults to OPENAI_API_KEY env var.
            base_url: Base URL for the API.
            model: Model to use.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

        if not self.api_key:
            logger.warning(
                "No API key provided. Set OPENAI_API_KEY env var or pass api_key."
            )

    def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Send a chat request to the LLM.

        Args:
            messages: List of chat messages.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences.

        Returns:
            LLMResponse with the model's response.

        Raises:
            LLMError: If the request fails.
        """
        if not self.api_key:
            raise LLMError(
                "No API key configured. Set OPENAI_API_KEY environment variable.",
                status_code=401,
            )

        # Convert messages to API format
        api_messages = [msg.to_dict() for msg in messages]

        # Build request payload
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if stop:
            payload["stop"] = stop

        # Make the request
        response = self._make_request(
            f"{self.base_url}/chat/completions", payload
        )

        # Parse response
        return self._parse_response(response)

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from a prompt.

        Args:
            prompt: The user prompt.
            system_message: Optional system message.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.

        Returns:
            LLMResponse with the generated text.
        """
        messages: List[ChatMessage] = []

        if system_message:
            messages.append(ChatMessage(ChatRole.SYSTEM, system_message))

        messages.append(ChatMessage(ChatRole.USER, prompt))

        return self.chat(messages, temperature, max_tokens)

    def _make_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        import urllib.request
        import urllib.error

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = json.dumps(payload).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=data, headers=headers)

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                error_data = json.loads(error_body)
                message = error_data.get("error", {}).get("message", str(e))
            except json.JSONDecodeError:
                message = error_body or str(e)

            raise LLMError(message, status_code=e.code)

        except urllib.error.URLError as e:
            raise LLMError(f"Network error: {e.reason}")

        except Exception as e:
            raise LLMError(f"Request failed: {e}")

    def _parse_response(self, response: Dict[str, Any]) -> LLMResponse:
        """Parse the API response."""
        if "error" in response:
            error = response["error"]
            raise LLMError(
                error.get("message", "Unknown error"),
                status_code=error.get("status"),
            )

        if "choices" not in response or not response["choices"]:
            raise LLMError("No choices in response")

        choice = response["choices"][0]
        message = choice.get("message", {})

        usage = response.get("usage", {})

        return LLMResponse(
            content=message.get("content", ""),
            model=response.get("model", self.model),
            usage=usage,
            finish_reason=choice.get("finish_reason"),
        )

    def stream(
        self,
        messages: List[ChatMessage],
        on_chunk: callable,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Stream a chat request and call on_chunk for each chunk.

        Args:
            messages: List of chat messages.
            on_chunk: Callback function for each chunk.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.

        Returns:
            LLMResponse with the complete response.
        """
        if not self.api_key:
            raise LLMError("No API key configured")

        api_messages = [msg.to_dict() for msg in messages]

        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        import urllib.request
        import urllib.error

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
        }

        data = json.dumps(payload).encode("utf-8")
        chunks = []

        try:
            req = urllib.request.Request(url=f"{self.base_url}/chat/completions", data=data, headers=headers)

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                for line in response:
                    line = line.decode("utf-8").strip()
                    if not line or not line.startswith("data:"):
                        continue

                    data_line = line[5:].strip()
                    if data_line == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_line)
                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                chunks.append(content)
                                on_chunk(content)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            raise LLMError(f"Stream failed: {e}")

        return LLMResponse(
            content="".join(chunks),
            model=self.model,
            usage={},
            finish_reason="stop",
        )


# Global client instance
_client: Optional[LLMClient] = None


def get_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMClient:
    """Get or create the global LLM client."""
    global _client

    if _client is None:
        from config import get_config

        config = get_config()
        _client = LLMClient(
            api_key=api_key or config.llm.api_key,
            base_url=config.llm.base_url,
            model=config.llm.model,
            timeout=config.llm.timeout,
        )

    return _client


def reset_client() -> None:
    """Reset the global client."""
    global _client
    _client = None
