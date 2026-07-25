from pathlib import Path

import pytest

from moza.config.models import MOZAConfig, AgentConfig


class TestGroqConfig:
    def test_groq_provider_in_config(self):
        config_path = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"
        assert config_path.exists(), f"config.yaml not found at {config_path}"

        config = MOZAConfig.from_yaml(config_path)
        assert "groq" in config.providers

    def test_groq_model_name(self):
        config_path = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"
        config = MOZAConfig.from_yaml(config_path)
        groq = config.providers["groq"]
        assert groq.model == "groq/llama-3.3-70b-versatile"

    def test_groq_has_api_key_ref(self):
        config_path = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"
        raw = config_path.read_text(encoding="utf-8")
        assert "${GROQ_API_KEY}" in raw or "gsk-" in raw

    def test_groq_base_url(self):
        config_path = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"
        config = MOZAConfig.from_yaml(config_path)
        groq = config.providers["groq"]
        assert groq.base_url == "https://api.groq.com/openai/v1"


class TestAgentConfig:
    def test_agent_config_default(self):
        cfg = AgentConfig()
        assert cfg.default == "mock"
        assert cfg.allowed_tools == []

    def test_agent_config_with_allowed_tools(self):
        cfg = AgentConfig(allowed_tools=["filesystem"])
        assert cfg.allowed_tools == ["filesystem"]

    def test_agents_in_moza_config(self):
        config = MOZAConfig(agents={
            "mock": AgentConfig(allowed_tools=[]),
            "openhands": AgentConfig(allowed_tools=["filesystem", "terminal", "browser"]),
        })
        assert "mock" in config.agents
        assert "openhands" in config.agents
        assert config.agents["mock"].allowed_tools == []
        assert config.agents["openhands"].allowed_tools == ["filesystem", "terminal", "browser"]

    def test_agent_config_from_yaml(self):
        config_path = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"
        if not config_path.exists():
            pytest.skip("config.yaml not found")
        config = MOZAConfig.from_yaml(config_path)
        assert hasattr(config, "agents")


class TestEnvExample:
    def test_env_example_has_groq_key(self):
        env_example = Path(__file__).resolve().parent.parent.parent.parent / "backend" / ".env.example"
        assert env_example.exists()
        content = env_example.read_text(encoding="utf-8")
        assert "GROQ_API_KEY" in content

    def test_env_example_has_openrouter_key(self):
        env_example = Path(__file__).resolve().parent.parent.parent.parent / "backend" / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        assert "OPENROUTER_API_KEY" in content
