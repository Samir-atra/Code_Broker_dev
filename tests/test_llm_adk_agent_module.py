"""Unit tests for ADK agent configuration and runner module in src/llm_adk_agent_module.py."""

import asyncio
import os
import pytest

from src import llm_adk_agent_module


def test_initialize_adk_model_missing_google_api_key(monkeypatch):
    """Tests that missing GOOGLE_API_KEY raises a ValueError."""
    monkeypatch.setattr(llm_adk_agent_module, "load_dotenv", lambda: None)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "mock_github_token")

    with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable not set."):
        asyncio.run(llm_adk_agent_module.initialize_adk_model())


def test_initialize_adk_model_missing_github_token(monkeypatch):
    """Tests that missing GITHUB_TOKEN raises a ValueError."""
    monkeypatch.setattr(llm_adk_agent_module, "load_dotenv", lambda: None)
    monkeypatch.setenv("GOOGLE_API_KEY", "mock_google_key")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    with pytest.raises(ValueError, match="GITHUB_TOKEN environment variable not set."):
        asyncio.run(llm_adk_agent_module.initialize_adk_model())


def test_initialize_adk_model_success(monkeypatch):
    """Tests successful initialization of LlmAgent with all expected tools attached."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123")
    monkeypatch.setenv("GITHUB_TOKEN", "test_token_456")

    agent = asyncio.run(llm_adk_agent_module.initialize_adk_model())

    assert agent.name == "helpful_assistant"
    assert agent.model == "gemini-2.0-flash"
    assert len(agent.tools) == 8

    # Verify tool names or functions attached
    tool_funcs = [t.func for t in agent.tools if hasattr(t, "func")]
    func_names = [f.__name__ for f in tool_funcs]

    assert "read_file" in func_names
    assert "read_directory_files" in func_names
    assert "read_github_repository" in func_names
    assert "get_linting_score" in func_names
    assert "get_security_score" in func_names
    assert "get_complexity_score" in func_names
    assert "get_test_score" in func_names
    assert "cleanup_temp_directory" in func_names


def test_generate_adk_response_mocked_runner(monkeypatch):
    """Tests generate_adk_response with a mocked runner execution."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    class MockRunner:
        def __init__(self, agent):
            self.agent = agent

        async def run_debug(self, prompt: str):
            return f"Mock response for: {prompt}"

    monkeypatch.setattr(llm_adk_agent_module, "InMemoryRunner", MockRunner)

    result = asyncio.run(llm_adk_agent_module.generate_adk_response("Inspect this module"))
    assert result == "Mock response for: Inspect this module"
