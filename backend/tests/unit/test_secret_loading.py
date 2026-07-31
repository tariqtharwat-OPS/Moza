import os
from unittest.mock import patch

import pytest

from moza_orchestrator.orchestrator import MozaOrchestrator, ENV_KEY_MAP


def _config(**overrides):
    cfg = {
        "ranking": [],
        "apiKeys": {},
        "baseURLs": {},
        "routing_rules": [],
        "fallback_chain": [],
    }
    cfg.update(overrides)
    return cfg


class TestSecretLoadingPhase1:
    """Phase 1 of ADR-006: env var takes precedence over config.json."""

    def test_env_var_takes_precedence(self):
        cfg = _config(apiKeys={"groq": "sk-config-key"})
        with patch.dict(os.environ, {"GROQ_API_KEY": "sk-env-key"}, clear=True):
            orch = MozaOrchestrator(ranking_config=cfg)
        assert orch.keys["groq"] == "sk-env-key"
        assert orch.key_lists["groq"] == ["sk-env-key"]

    def test_config_is_fallback_when_no_env(self):
        cfg = _config(apiKeys={"groq": "sk-config-key"})
        with patch.dict(os.environ, {}, clear=True):
            orch = MozaOrchestrator(ranking_config=cfg)
        assert orch.keys["groq"] == "sk-config-key"

    def test_no_key_warns(self):
        """Provider with no env var and no config entry gets no key."""
        cfg = _config(apiKeys={"groq": "sk-config"})
        with patch.dict(os.environ, {}, clear=True):
            orch = MozaOrchestrator(ranking_config=cfg)
        assert "cerebras" not in orch.keys
        assert orch.keys.get("groq") == "sk-config"

    def test_all_providers_have_env_var_mapping(self):
        """Every provider in a representative apiKeys config has an ENV_KEY_MAP entry."""
        providers_in_keys = {
            "groq", "github", "openrouter", "mistral",
            "sambanova", "nvidia", "zhipu", "cerebras",
            "cloudflare", "opencode-zen",
        }
        mapped = set(ENV_KEY_MAP.keys())
        missing = providers_in_keys - mapped
        assert not missing, f"Providers missing from ENV_KEY_MAP: {missing}"

    def test_named_accounts_skipped_when_env_set(self):
        """Even dict-style apiKeys entries (named accounts) are skipped when env var exists."""
        cfg = _config(apiKeys={
            "nvidia": {
                "Tharwat": "nvapi-config-tharwat",
                "OPS": "nvapi-config-ops",
            }
        })
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "nvapi-env"}, clear=True):
            orch = MozaOrchestrator(ranking_config=cfg)
        assert orch.keys["nvidia"] == "nvapi-env"
        assert len(orch.key_lists["nvidia"]) == 1

    def test_cloudflare_env_var(self):
        """Cloudflare env var uses account_id|token format (same as config.json composite)."""
        cfg = _config(apiKeys={"cloudflare": {"OPS": {"account_id": "cfg-id", "token": "cfg-tok"}}})
        with patch.dict(os.environ, {"CLOUDFLARE_API_KEY": "env-id|env-tok"}, clear=True):
            orch = MozaOrchestrator(ranking_config=cfg)
        assert orch.keys["cloudflare"] == "env-id|env-tok"

    def test_env_var_applies_to_correct_provider(self):
        """GROQ_API_KEY maps to 'groq' provider, not any other."""
        cfg = _config(apiKeys={"groq": "sk-groq", "nvidia": "nvapi-nvidia"})
        with patch.dict(os.environ, {"GROQ_API_KEY": "sk-env"}, clear=True):
            orch = MozaOrchestrator(ranking_config=cfg)
        assert orch.keys["groq"] == "sk-env"
        assert orch.keys["nvidia"] == "nvapi-nvidia"

    def test_empty_env_var_does_not_override(self):
        """An explicitly set but empty env var should not override config."""
        cfg = _config(apiKeys={"mistral": "sk-mistral-config"})
        with patch.dict(os.environ, {"MISTRAL_API_KEY": ""}, clear=True):
            orch = MozaOrchestrator(ranking_config=cfg)
        assert orch.keys["mistral"] == "sk-mistral-config"
