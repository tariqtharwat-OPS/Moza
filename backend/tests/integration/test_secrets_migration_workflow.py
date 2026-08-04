"""ADR-007 Phase 2 workflow test: auto-migrate .env keys to encrypted vault."""
import json
from pathlib import Path

import pytest

from moza.core.secrets_manager import SecretsManager
from moza.core.secrets_migration import ENV_TO_VAULT_MAP, SecretsMigration

SAMPLE_ENV = """# LLM Provider API Keys
GROQ_MOZA_API_KEY=sk-groq-real-key
GROQ_YOUSSEF_API_KEY=sk-groq-youssef
GITHUB_MODELS_API_KEY=github_pat_abc123
OPENROUTER_API_KEY=sk-or-v1-openrouter
MISTRAL_API_KEY=r689mistralsecret
NVIDIA_API_KEY=nvapi-nvidia-secret
GLM_ZHIPU_API_KEY=glm-zhipu-secret

# Non-secret
DATABASE_URL=postgres://user:pass@localhost/db
"""


def _setup(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV, encoding="utf-8")
    sm = SecretsManager(str(tmp_path / "secrets.enc"))
    sm.initialize()
    return env_file, sm


def test_detects_env_file_and_reads_real_var_names(tmp_path):
    env_file, sm = _setup(tmp_path)
    mig = SecretsMigration(sm, env_path=str(env_file))
    assert mig.detect_env_file() is True
    keys = mig.read_env_keys()
    assert keys["groq"] == "sk-groq-real-key"
    assert keys["github"] == "github_pat_abc123"
    assert keys["zhipu"] == "glm-zhipu-secret"
    assert keys["openrouter"] == "sk-or-v1-openrouter"
    assert "groq_youssef" not in keys  # secondary groq key not in map


def test_missing_env_file_returns_empty(tmp_path):
    sm = SecretsManager(str(tmp_path / "secrets.enc"))
    sm.initialize()
    mig = SecretsMigration(sm, env_path=str(tmp_path / "nope.env"))
    assert mig.detect_env_file() is False
    assert mig.read_env_keys() == {}
    summary = mig.run_full_migration()
    assert summary["env_detected"] is False


def test_full_migration_roundtrip(tmp_path):
    env_file, sm = _setup(tmp_path)
    mig = SecretsMigration(sm, env_path=str(env_file))

    summary = mig.run_full_migration(comment_out=True)

    assert summary["env_detected"] is True
    assert summary["keys_found"] == 6
    assert summary["migrated"] == 6
    assert summary["skipped"] == 0
    assert summary["failed"] == 0
    assert summary["commented_out"] == 6

    # Keys decrypted correctly from vault
    assert sm.decrypt_secret("groq") == "sk-groq-real-key"
    assert sm.decrypt_secret("openrouter") == "sk-or-v1-openrouter"
    assert sm.decrypt_secret("mistral") == "r689mistralsecret"

    # .env lines commented out
    content = env_file.read_text(encoding="utf-8")
    for var in [
        "GROQ_MOZA_API_KEY",
        "GITHUB_MODELS_API_KEY",
        "OPENROUTER_API_KEY",
        "MISTRAL_API_KEY",
        "NVIDIA_API_KEY",
        "GLM_ZHIPU_API_KEY",
    ]:
        assert f"# {var}=" in content or f"  # {var}=" in content


def test_vault_contains_no_plaintext_after_migration(tmp_path):
    env_file, sm = _setup(tmp_path)
    mig = SecretsMigration(sm, env_path=str(env_file))
    mig.run_full_migration(comment_out=False)

    raw = (tmp_path / "secrets.enc").read_text(encoding="utf-8")
    assert "sk-groq-real-key" not in raw
    assert "github_pat_abc123" not in raw
    assert "nvapi-nvidia-secret" not in raw
    env = json.loads(raw)
    assert env["cipher"] == "AES-256-GCM"
    assert sm.is_vault_encrypted


def test_rerun_migration_skips_existing(tmp_path):
    env_file, sm = _setup(tmp_path)
    mig = SecretsMigration(sm, env_path=str(env_file))

    first = mig.run_full_migration(comment_out=True)
    second = mig.run_full_migration(comment_out=True)

    assert first["migrated"] == 6
    assert second["migrated"] == 0
    assert second["skipped"] == 6
    assert second["commented_out"] == 0

    # No duplicates in vault (decrypt returns single value)
    assert sm.decrypt_secret("groq") == "sk-groq-real-key"


def test_comment_out_preserves_line_endings(tmp_path):
    env_file, sm = _setup(tmp_path)
    mig = SecretsMigration(sm, env_path=str(env_file))
    mig.run_full_migration(comment_out=True)
    content = env_file.read_bytes()
    assert b"\r\n" in content or b"\n" in content


def test_migration_map_covers_all_orchestrator_providers():
    from moza_orchestrator.orchestrator import ENV_KEY_MAP

    mapped = set(ENV_TO_VAULT_MAP.keys())
    orchestrator = set(ENV_KEY_MAP.keys())
    assert orchestrator.issubset(mapped), (
        f"Missing providers in migration map: {orchestrator - mapped}"
    )
