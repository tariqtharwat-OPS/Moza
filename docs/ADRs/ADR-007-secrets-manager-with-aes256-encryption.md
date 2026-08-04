# ADR-007: Secrets Manager with AES-256 Encryption

## Status
**Proposed**

## Date
2026-08-01

## Context

The current secret loading strategy (ADR-006 Phase 1) loads API keys from environment variables only, sourced from `backend/.env`. While this satisfies Principle 12.5's "secrets outside version control" requirement, it leaves a critical gap:

- **Plaintext at rest:** API keys are stored in plain text in `backend/.env` on disk. Anyone with filesystem access can read all provider credentials.
- **No encryption:** There is no encryption at rest for secrets.
- **Level A Security Baseline violation:** The Level A Security Baseline mandates encrypted secret storage (see `docs/MOZA_MASTER_PLAN.md` Section 12.5). Plaintext `.env` storage does not meet this bar.

This violates:
- **Principle 12.5 (Secret Isolation):** Secrets must be isolated and protected, not merely excluded from Git.
- **Principle 8 (Audit Logging):** All secret access must be auditable — currently there is no record of who/what accessed a key and when.
- **Level A Security Baseline:** Encrypted secret storage is a key deliverable.

## Decision

Implement a Secrets Manager component that:

1. **Encrypts all API keys with AES-256-GCM** before storing to disk (authenticated encryption — confidentiality + integrity).
2. **Derives a master key** from a combination of:
   - Machine-specific identifier (hardware ID, so the vault is bound to the installation machine)
   - User-provided passphrase (optional, for extra security)
   - Random salt (per-installation, stored alongside the vault)
3. **Stores encrypted secrets** in `backend/secrets.enc` (binary file, **NOT** in Git).
4. **Exposes the API:**
   - `encrypt_secret(key, value)` — encrypt and store a secret
   - `decrypt_secret(key)` — decrypt and return a stored secret
   - `rotate_secret(key, new_value)` — re-encrypt a secret with a new value
5. **Integrates with existing env var loading:** dual-read in Phase 1; auto-migrates `.env` keys into the encrypted vault on first run (Phase 2).
6. **Adds audit logging** for all secret access (Principle 8 compliance) — log each encrypt/decrypt/rotate operation to the event bus / audit trail.

### Key Derivation (PBKDF2)

- Master key derived via **PBKDF2-HMAC-SHA256** with **100,000 iterations minimum**.
- Per-vault random 16-byte salt prevents rainbow-table attacks and ties the vault to one installation.
- Optional user passphrase is mixed into the derivation (passphrase unknown → vault unreadable even with the hardware ID).
- The derived key is used only as the AES-256-GCM key; it is NEVER persisted in plaintext.

### Vault Format (`backend/secrets.enc`)

Binary container (JSON envelope + encrypted payload):
```
{
  "version": 1,
  "kdf": "PBKDF2-HMAC-SHA256",
  "iterations": 100000,
  "salt": "<base64>",
  "cipher": "AES-256-GCM",
  "nonce": "<base64>",
  "ciphertext": "<base64>",      # JSON dict {key: plaintext}
  "auth_tag": "<base64>"
}
```
AES-GCM provides authenticated encryption: any tampering with the ciphertext is detected on decryption (auth tag mismatch).

### Audit Logging

Every vault operation emits an audit event (via the existing EventBus):
- `secret_encrypted` — key name (never the value)
- `secret_decrypted` — key name, caller context
- `secret_rotated` — key name
- `secret_access_denied` — on auth tag / passphrase failure (potential tamper or intrusion)

Logs record key *names*, timestamps, and operation type — never secret values.

## Migration Plan

| Phase | Duration | Change | Tests Required |
|-------|----------|--------|----------------|
| Phase 1 | 1 day | Add SecretsManager alongside env var loading (dual-read) | Existing suite + new unit tests |
| Phase 2 | 1 day | Auto-migrate `.env` keys to `secrets.enc` on first run | Migration tests + existing suite |
| Phase 3 | 1 day | Deprecate `.env` loading with warning | Existing suite |
| Phase 4 | 1 day | Remove `.env` loading entirely | Existing suite + benchmark |

Each phase must pass the existing backend test suite before proceeding.

## Security Considerations

- **Master key NEVER stored in plaintext** — derived at runtime from hardware ID (+ optional passphrase) + salt.
- Use the `cryptography` library (Python, well-audited, maintained).
- Add `backend/secrets.enc` to `.gitignore` so the vault can never be committed.
- **PBKDF2 with ≥100,000 iterations** (OWASP recommendation) for key derivation.
- Key file permissions: restrict `secrets.enc` to the owning user where the OS permits.
- If the hardware ID changes (new machine / reinstall), the vault becomes unreadable — document the recovery path (export/import via passphrase) in the implementation.

## Consequences

### Positive
- Full compliance with Principle 12.5 and the Level A Security Baseline (encryption at rest).
- Principle 8 compliance — auditable secret access.
- Protection against plaintext credential theft from disk.
- Single, consistent interface for secret lifecycle (encrypt/decrypt/rotate).
- Smooth migration via dual-read → auto-migrate → deprecate → remove.

### Negative
- Added complexity (cryptography dependency, key derivation, vault management).
- Secrets unavailable if hardware ID or passphrase is lost (mitigated by documented recovery path).
- Small performance cost per decrypt (~100k PBKDF2 iterations) — negligible for per-request provider key access given session caching.

### Risks
- Hardware ID changes could lock out the vault (mitigated by passphrase-based recovery + salt backup).
- Misconfigured file permissions could weaken protection (mitigated by restrictive chmod on creation).
- Rollout to production environments must follow the same phased migration.

## Compliance
- [x] Backward compatibility addressed (dual-read in Phase 1)
- [x] Migration plan included
- [x] Interfaces defined (SecretsManager ABC with `encrypt_secret` / `decrypt_secret` / `rotate_secret`)
- [ ] Tests (pending implementation)
- [ ] Documentation (this ADR)
- [ ] Manager approval (PENDING)

## Related Documents
- `docs/MOZA_MASTER_PLAN.md` Section 12.5 — Level A Security Baseline (Secret Isolation)
- `docs/ADRs/ADR-006-standardize-provider-rotation-and-secret-isolation.md` — Preceding ADR (env-only secret loading)
- `docs/ADRs/ADR-005-resolve-level-a-audit-contradiction.md` — Level A deliverable tracking
- `backend/.env` — Current plaintext secret store (to be migrated)
