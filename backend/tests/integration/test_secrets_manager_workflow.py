"""ADR-007 Phase 1 workflow test: Secrets Manager (AES-256-GCM, dual-read)."""
import json
import os
from pathlib import Path

import pytest

from moza.core.secrets_manager import SecretsManager


def _manager(tmp_path, **kwargs):
    m = SecretsManager(str(tmp_path / "secrets.enc"), **kwargs)
    m.initialize()
    return m


def test_encrypt_decrypt_three_keys_roundtrip(tmp_path):
    m = _manager(tmp_path)
    m.encrypt_secret("groq", "sk-groq-abc")
    m.encrypt_secret("nvidia", "nvapi-xyz")
    m.encrypt_secret("github", "github_123")
    assert m.decrypt_secret("groq") == "sk-groq-abc"
    assert m.decrypt_secret("nvidia") == "nvapi-xyz"
    assert m.decrypt_secret("github") == "github_123"
    assert m.decrypt_secret("missing") is None


def test_vault_contains_no_plaintext(tmp_path):
    m = _manager(tmp_path)
    m.encrypt_secret("groq", "sk-super-secret-value")
    raw = (tmp_path / "secrets.enc").read_text(encoding="utf-8")
    assert "sk-super-secret-value" not in raw
    assert "groq" not in raw
    env = json.loads(raw)
    assert env["cipher"] == "AES-256-GCM"
    assert env["ciphertext"] and env["nonce"] and env["salt"]
    assert m.is_vault_encrypted


def test_dual_read_vault_precedence_over_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "sk-env-value")
    m = _manager(tmp_path)
    m.encrypt_secret("groq", "sk-vault-value")
    assert m.get_secret("groq", "GROQ_API_KEY") == "sk-vault-value"


def test_dual_read_falls_back_to_env_when_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "sk-mistral-env")
    m = _manager(tmp_path)
    m.encrypt_secret("groq", "sk-vault-value")
    assert m.get_secret("mistral", "MISTRAL_API_KEY") == "sk-mistral-env"


def test_migrate_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "sk-groq-migrated")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-migrated")
    m = _manager(tmp_path)
    count = m.migrate_from_env({"groq": "GROQ_API_KEY", "nvidia": "NVIDIA_API_KEY"})
    assert count == 2
    assert m.decrypt_secret("groq") == "sk-groq-migrated"
    assert m.decrypt_secret("nvidia") == "nvapi-migrated"


def test_migrate_skips_existing_secrets(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "sk-new-value")
    m = _manager(tmp_path)
    m.encrypt_secret("groq", "sk-existing")
    count = m.migrate_from_env({"groq": "GROQ_API_KEY"})
    assert count == 0
    assert m.decrypt_secret("groq") == "sk-existing"


def test_rotate_secret(tmp_path):
    m = _manager(tmp_path)
    m.encrypt_secret("groq", "sk-old")
    m.rotate_secret("groq", "sk-new")
    assert m.decrypt_secret("groq") == "sk-new"


def test_vault_path_ignored_by_gitignore():
    gitignore = Path(__file__).resolve().parents[3] / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert "backend/secrets.enc" in content
    assert "*.key" in content
    assert "*.secret" in content
