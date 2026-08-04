"""
Secrets Migration: Auto-migrate .env keys to encrypted vault (ADR-007 Phase 2).

Reads API keys from backend/.env and encrypts them into the AES-256-GCM vault.
On success, migrated lines are commented out in .env (never deleted, reversible).

The map supports multiple candidate env var names per vault key so that both the
legacy names (e.g. GROQ_API_KEY) and the real names found in backend/.env
(e.g. GROQ_MOZA_API_KEY) are detected during migration.
"""
import os
import re
from pathlib import Path
from typing import Dict, List

from .secrets_manager import SecretsManager

# Map of vault key names (provider, matching orchestrator ENV_KEY_MAP) to the
# .env variable names that may hold the secret. First match wins.
ENV_TO_VAULT_MAP: Dict[str, List[str]] = {
    "groq": ["GROQ_MOZA_API_KEY", "GROQ_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],
    "sambanova": ["SAMBANOVA_API_KEY"],
    "nvidia": ["NVIDIA_API_KEY"],
    "github": ["GITHUB_MODELS_API_KEY", "GITHUB_PAT", "GITHUB_API_KEY"],
    "zhipu": ["GLM_ZHIPU_API_KEY", "ZHIPU_API_KEY", "GLM_API_KEY"],
    "cerebras": ["CEREBRAS_API_KEY"],
    "cloudflare": ["CLOUDFLARE_API_KEY"],
    "opencode-zen": ["OPENCODE_ZEN_API_KEY"],
}


class SecretsMigration:
    def __init__(self, secrets_manager: SecretsManager, env_path: str = "backend/.env"):
        self.secrets_manager = secrets_manager
        self.env_path = Path(env_path)

    def detect_env_file(self) -> bool:
        """Check if .env file exists."""
        return self.env_path.exists()

    def _find_env_var(self, env_content: str, env_var: str) -> str | None:
        """Return the raw value of ENV_VAR in env_content, or None.

        Matches both plain lines (``ENV_VAR=value``) and lines previously
        commented out by this migration (``# ENV_VAR=value  # Migrated ...``),
        so a re-run can still report keys as skipped instead of missing.
        """
        value_pattern = r"['\"]?([^'\r\n\"]+)['\"]?"
        # Plain (uncommented) assignment.
        pattern = rf"^(?:#\s*)?{re.escape(env_var)}\s*=\s*{value_pattern}"
        match = re.search(pattern, env_content, re.MULTILINE)
        return match.group(1) if match else None

    def read_env_keys(self) -> Dict[str, str]:
        """Read API keys from .env file."""
        if not self.detect_env_file():
            return {}

        env_content = self.env_path.read_text(encoding="utf-8")
        keys: Dict[str, str] = {}

        for vault_key, env_vars in ENV_TO_VAULT_MAP.items():
            for env_var in env_vars:
                value = self._find_env_var(env_content, env_var)
                if value:
                    keys[vault_key] = value
                    break

        return keys

    def migrate_keys(self) -> Dict[str, str]:
        """
        Migrate keys from .env to encrypted vault.
        Returns dict of {key: status} where status is
        "migrated", "skipped_exists", or "failed: <error>".
        """
        env_keys = self.read_env_keys()
        results: Dict[str, str] = {}

        for vault_key, value in env_keys.items():
            try:
                existing = self.secrets_manager.decrypt_secret(vault_key)
                if existing:
                    results[vault_key] = "skipped_exists"
                    continue

                self.secrets_manager.encrypt_secret(vault_key, value)
                results[vault_key] = "migrated"
            except Exception as e:
                results[vault_key] = f"failed: {str(e)}"

        return results

    def comment_out_migrated_keys(self, migrated_keys: List[str]) -> int:
        """
        Comment out migrated keys in .env file (line endings preserved).
        Returns count of commented lines.
        """
        if not self.detect_env_file():
            return 0

        env_content = self.env_path.read_text(encoding="utf-8")
        lines = env_content.splitlines(keepends=True)
        commented = 0

        for vault_key in migrated_keys:
            env_vars = ENV_TO_VAULT_MAP.get(vault_key)
            if not env_vars:
                continue

            for env_var in env_vars:
                for i, line in enumerate(lines):
                    stripped = line.lstrip()
                    if stripped.startswith(f"{env_var}=") and not stripped.startswith("#"):
                        indent = line[: len(line) - len(stripped)]
                        newline = "\r\n" if line.endswith("\r\n") else "\n"
                        body = line.rstrip("\r\n")
                        lines[i] = (
                            f"{indent}# {body}  # Migrated to encrypted vault (ADR-007){newline}"
                        )
                        commented += 1
                        break

        self.env_path.write_text("".join(lines), encoding="utf-8")
        return commented

    def run_full_migration(self, comment_out: bool = True) -> Dict:
        """
        Run complete migration process.
        Returns summary dict.
        """
        summary = {
            "env_detected": self.detect_env_file(),
            "keys_found": 0,
            "migrated": 0,
            "skipped": 0,
            "failed": 0,
            "commented_out": 0,
        }

        if not summary["env_detected"]:
            return summary

        env_keys = self.read_env_keys()
        summary["keys_found"] = len(env_keys)

        results = self.migrate_keys()
        for status in results.values():
            if status == "migrated":
                summary["migrated"] += 1
            elif status == "skipped_exists":
                summary["skipped"] += 1
            else:
                summary["failed"] += 1

        if comment_out:
            migrated_keys = [k for k, v in results.items() if v == "migrated"]
            summary["commented_out"] = self.comment_out_migrated_keys(migrated_keys)

        return summary
