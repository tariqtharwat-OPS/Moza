# ADR-010: Secure Backup Manager

## Status: Proposed

## Context
The Moza system currently lacks a secure backup mechanism for critical files such as session data, audit logs, and secrets. Without backups, data loss due to system failures or accidental deletions could lead to significant operational disruptions.

## Decision
Implement a **Secure Backup Manager** that:
- Encrypts backups using **Fernet (AES-128-CBC + HMAC)** derived from the SecretsManager master key.
- Targets critical files: `sessions/`, `audit_log.jsonl`, and `secrets.enc`.
- Uses `.tar.gz.enc` format with a manifest file containing SHA-256 checksums for each file.
- Supports scheduled backups (default: 24 hours) and retention policy (default: 7 days).
- Provides restore functionality with pre-restore snapshots.

## Implementation Details
- **Encryption**: Use `cryptography.fernet` for encryption, with the key derived from SecretsManager.
- **Backup Format**: `.tar.gz.enc` with a manifest file containing SHA-256 checksums.
- **Scheduling**: Use `asyncio` for scheduling backups with a cancellable task.
- **Retention Policy**: Keep only the last 7 backups, with pre-restore snapshots retained.

## Crypto Scheme
- **Fernet** (AES-128-CBC + HMAC) for encryption.
- **Key Derivation**: Use HKDF from SecretsManager master key.
- **Manifest**: JSON file with SHA-256 checksums for each file inside the archive.

## Targets
- `sessions/` directory
- `audit_log.jsonl` file
- `secrets.enc` file

## Backup Format
- `.tar.gz.enc` encrypted archive
- Manifest file with SHA-256 checksums

## Scheduling
- Default interval: 24 hours
- Cancellable asyncio task

## Retention Policy
- Default retention: 7 days
- Keep only the last 7 backups
- Pre-restore snapshots are retained indefinitely

## Consequences
- **Security**: Ensures data is encrypted and protected from unauthorized access.
- **Reliability**: Prevents data loss due to system failures or accidental deletions.
- **Maintainability**: Easy to integrate with existing SecretsManager and audit logging systems.

## References
- [Fernet Documentation](https://cryptography.io/en/latest/fernet/)
- [Python Tarfile](https://docs.python.org/3/library/tarfile.html)

---