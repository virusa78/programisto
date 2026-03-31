"""Unit tests for LLM gateway."""

import pytest
from llm.client import LLMClient, ChatMessage, ChatRole, LLMResponse, LLMError
from tests.fixtures.mock_llm import MockLLMClient


class TestChatMessage:
    """Tests for ChatMessage class."""

    def test_message_creation(self):
        """Test creating a chat message."""
        message = ChatMessage(
            role=ChatRole.USER,
            content="Hello, world!",
        )

        assert message.role == ChatRole.USER
        assert message.content == "Hello, world!"

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        message = ChatMessage(
            role=ChatRole.USER,
            content="Test",
            name="test-user",
        )

        data = message.to_dict()
        assert data["role"] == "user"
        assert data["content"] == "Test"
        assert data["name"] == "test-user"


class TestLLMResponse:
    """Tests for LLMResponse class."""

    def test_response_creation(self):
        """Test creating an LLM response."""
        response = LLMResponse(
            content="Hello from LLM",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )

        assert response.content == "Hello from LLM"
        assert response.model == "test-model"

    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        response = LLMResponse(
            content="Test",
            model="test",
            usage={"total_tokens": 30},
            finish_reason="stop",
        )

        data = response.to_dict()
        assert data["content"] == "Test"
        assert data["finish_reason"] == "stop"


class TestLLMClient:
    """Tests for LLMClient class."""

    def test_init(self):
        """Test client initialization."""
        client = LLMClient(
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model",
        )

        assert client.api_key == "test-key"
        assert client.base_url == "https://api.test.com"
        assert client.model == "test-model"

    def test_no_api_key(self):
        """Test client without API key."""
        client = LLMClient()
        assert client.api_key is None

    def test_chat_with_mock(self, mock_llm):
        """Test chat with mock client."""
        messages = [
            ChatMessage(ChatRole.SYSTEM, "You are helpful"),
            ChatMessage(ChatRole.USER, "Hello"),
        ]

        response = mock_llm.chat(messages)
        assert response.content == "Mock LLM response"
        assert mock_llm.get_call_count() == 1

    def test_generate_with_mock(self, mock_llm):
        """Test generate with mock client."""
        response = mock_llm.generate(
            prompt="What is 2+2?",
            system_message="You are a math helper",
        )

        assert response.content == "Mock LLM response"

    def test_chat_with_callback(self):
        """Test chat with dynamic response callback."""
        def callback(messages):
            return "Dynamic response"

        client = MockLLMClient()
        client.set_callback(callback)

        response = client.chat([ChatMessage(ChatRole.USER, "test")])
        assert response.content == "Dynamic response"

    def test_chat_fails_without_api_key(self):
        """Test that chat fails without API key on real client."""
        client = LLMClient()
        with pytest.raises(LLMError):
            client.chat([ChatMessage(ChatRole.USER, "test")])


class TestLLMError:
    """Tests for LLMError class."""

    def test_error_creation(self):
        """Test creating an LLM error."""
        error = LLMError("Connection failed", status_code=500)

        assert error.message == "Connection failed"
        assert error.status_code == 500

    def test_error_str(self):
        """Test error string representation."""
        error = LLMError("Test error")
        assert str(error) == "Test error"
