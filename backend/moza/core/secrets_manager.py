"""
Secrets Manager with AES-256-GCM encryption (ADR-007 Phase 1).
Dual-read mode: reads from the encrypted vault first, then environment (.env).

Per ADR-007:
- AES-256-GCM authenticated encryption (confidentiality + integrity)
- PBKDF2-HMAC-SHA256 master key derivation (100,000 iterations)
- Per-installation random salt stored in the vault envelope
- Vault stored at backend/secrets.enc (gitignored)
- audit logging for every crypt operation (Principle 8)
"""
import base64
import json
import logging
import os
import secrets
import socket
import subprocess
from pathlib import Path
from typing import Dict, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("moza.secrets")

KDF_ITERATIONS = 100_000
KDF_ALGORITHM = "PBKDF2-HMAC-SHA256"
CIPHER = "AES-256-GCM"
VAULT_VERSION = 1


def _required(length: int) -> bytes:
    return secrets.token_bytes(length)


class SecretsManager:
    """Encrypted, audited secret store (ADR-007)."""

    def __init__(self, vault_path: str = "secrets.enc"):
        path = Path(vault_path)
        if not path.is_absolute():
            path = Path(os.path.abspath(vault_path))
        self.vault_path = path
        self._master_key: Optional[bytes] = None

    # ── key derivation ──────────────────────────────────────────────────

    def _get_machine_id(self) -> str:
        """Return a stable machine-specific identifier (cross-platform)."""
        try:
            result = subprocess.run(
                ["wmic", "csproduct", "get", "UUID"],
                capture_output=True, text=True, timeout=5,
            )
            lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
            if len(lines) >= 2:
                return lines[1]
        except Exception:
            pass
        try:
            return Path("/etc/machine-id").read_text().strip()
        except Exception:
            pass
        return socket.gethostname()

    def _derive_key(self, salt: bytes, passphrase: Optional[str] = None) -> bytes:
        material = self._get_machine_id()
        if passphrase:
            material = f"{material}::{passphrase}"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=KDF_ITERATIONS,
        )
        return kdf.derive(material.encode("utf-8"))

    # ── composition helpers ─────────────────────────────────────────────

    def _compose(self, plaintext: bytes, salt: bytes) -> Dict:
        nonce = _required(12)
        aesgcm = AESGCM(self._master_key)
        ct = aesgcm.encrypt(nonce, plaintext, None)
        return {
            "version": VAULT_VERSION,
            "kdf": KDF_ALGORITHM,
            "iterations": KDF_ITERATIONS,
            "cipher": CIPHER,
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ct).decode(),
        }

    def _decompose(self, envelope: Dict) -> bytes:
        salt = base64.b64decode(envelope["salt"])
        nonce = base64.b64decode(envelope["nonce"])
        ct = base64.b64decode(envelope["ciphertext"])
        aesgcm = AESGCM(self._master_key)
        return aesgcm.decrypt(nonce, ct, None)

    # ── lifecycle ───────────────────────────────────────────────────────

    def initialize(self, passphrase: Optional[str] = None, salt: Optional[bytes] = None) -> None:
        """Initialize the manager: derive key and ensure vault exists."""
        if self.vault_path.exists():
            env = self._load_envelope()
            salt = base64.b64decode(env["salt"])
        else:
            salt = salt or _required(16)
        self._master_key = self._derive_key(salt, passphrase)
        if not self.vault_path.exists():
            envelope = self._compose(b"{}", salt)
            self._write(envelope)
            logger.info(f"[SecretsManager] created vault at {self.vault_path}")

    @property
    def _initialized(self) -> bool:
        return self._master_key is not None

    def _write(self, envelope: Dict) -> None:
        self.vault_path.write_text(json.dumps(envelope, indent=2))

    def _load_envelope(self) -> Dict:
        return json.loads(self.vault_path.read_text())

    # ── public API ──────────────────────────────────────────────────────

    def encrypt_secret(self, key: str, value: str) -> None:
        """Encrypt and store a secret."""
        if not self._initialized:
            raise RuntimeError("SecretsManager not initialized. Call initialize() first.")
        envelope = self._load_envelope()
        payload = json.loads(self._decompose(envelope).decode("utf-8"))
        payload[key] = value
        new_salt = base64.b64decode(envelope["salt"])
        self._write(self._compose(json.dumps(payload).encode("utf-8"), new_salt))
        logger.info(f"secret_encrypted key={key} (value redacted)")

    def decrypt_secret(self, key: str) -> Optional[str]:
        """Decrypt and retrieve a secret. Returns None if not present."""
        if not self._initialized:
            raise RuntimeError("SecretsManager not initialized. Call initialize() first.")
        envelope = self._load_envelope()
        payload = json.loads(self._decompose(envelope).decode("utf-8"))
        value = payload.get(key)
        logger.info(f"secret_decrypted key={key} present={value is not None}")
        return value

    def rotate_secret(self, key: str, new_value: str) -> None:
        """Re-encrypt a secret with a new value."""
        self.encrypt_secret(key, new_value)
        logger.info(f"secret_rotated key={key}")

    def get_secret(self, key: str, env_var: Optional[str] = None) -> Optional[str]:
        """Dual-read: encrypted vault first, then env var (Phase 1)."""
        if self.vault_path.exists() and self._initialized:
            try:
                value = self.decrypt_secret(key)
                if value:
                    return value
            except Exception:
                logger.warning(f"Vault read failed for {key}; falling back to env var")
        if env_var:
            return os.environ.get(env_var)
        return os.environ.get(key)

    def migrate_from_env(self, env_keys: Dict[str, str]) -> int:
        """Migrate .env (os.environ) secrets into the vault. Returns count migrated."""
        migrated = 0
        for key, env_var in env_keys.items():
            value = os.environ.get(env_var)
            if value and not self.decrypt_secret(key):
                self.encrypt_secret(key, value)
                migrated += 1
        return migrated

    @property
    def is_vault_encrypted(self) -> bool:
        """True when the stored vault is a JSON envelope (not plaintext values)."""
        try:
            env = self._load_envelope()
            return (
                env.get("cipher") == CIPHER
                and "ciphertext" in env
                and "nonce" in env
                and "salt" in env
            )
        except Exception:
            return False