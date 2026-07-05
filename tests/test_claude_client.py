from unittest.mock import Mock, patch

import pytest

from backend.ai.claude_client import ClaudeClient, ClaudeClientError


@patch("backend.ai.claude_client.Anthropic")
def test_client_uses_env_key_and_builds_prompt(mock_anthropic):
    mock_client = Mock()
    mock_client.messages.create.return_value = Mock(content=[Mock(text="hello from claude")])
    mock_anthropic.return_value = mock_client

    with patch("backend.ai.claude_client.os.getenv", side_effect=lambda key, default=None: "test-key" if key == "ANTHROPIC_API_KEY" else default):
        client = ClaudeClient(model_name="claude-sonnet-4-6")
        response = client.send_prompt("Say hi")

    assert response == "hello from claude"
    mock_client.messages.create.assert_called_once()


def test_missing_key_raises_meaningful_error():
    with patch("backend.ai.claude_client.os.getenv", return_value=None):
        with pytest.raises(ClaudeClientError, match="ANTHROPIC_API_KEY"):
            ClaudeClient()
