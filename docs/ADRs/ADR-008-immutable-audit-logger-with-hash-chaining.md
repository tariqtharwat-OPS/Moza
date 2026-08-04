# ADR-008: Immutable Audit Logger with Hash Chaining

## Status
**Proposed**

## Date
2026-08-04

## Context

The Secrets Manager (ADR-007) now emits audit events to the EventBus (`secret_encrypted`, `secret_decrypted`, `secret_rotated`), and the orchestrator publishes `provider_failed` / `provider_recovered` events. However, there is **no persistent, tamper-proof storage** for these events:

- **Ephemeral:** EventBus events are in-memory and vanish on restart — there is no durable record of who accessed a secret or when a provider failed.
- **Not immutable:** Even if events were written to a plain log file, an attacker (or accidental edit) could alter or delete past entries with no detectable trace.
- **Level A Security Baseline violation:** The Level A Security Baseline and Principle 8 (Audit Logging) mandate *immutable records of system actions* — append-only, tamper-evident, and verifiable.

This violates:
- **Principle 8 (Audit Logging):** System actions must be recorded in an immutable, auditable trail.
- **Level A Security Baseline:** An append-only, cryptographically chained audit log is a key deliverable.

## Decision

Implement an `AuditLogger` component that:

1. **Immutable Storage:** Appends events to a JSONL file (`backend/audit_log.jsonl`), one JSON object per line. The file is append-only by design (each entry references the one before it).

2. **Cryptographic Hash Chaining:**
   - Every entry contains:
     - `ts` — ISO-8601 UTC timestamp
     - `event` — event type (e.g. `secret_accessed`, `provider_failed`, `tool_executed`)
     - `payload` — sanitized event data (never secret values; key *names* only)
     - `prev_hash` — SHA-256 hex digest of the **previous** entry (the entire previous JSON line)
     - `hash` — SHA-256 hex digest of the current entry's own content (excluding the `hash` field itself)
   - The **first entry** uses a hardcoded `genesis_hash` (a fixed constant) as its `prev_hash`, anchoring the chain.
   - Consequence: altering, deleting, or reordering any past entry changes its `hash`, which breaks the `prev_hash` of every subsequent entry — tampering is mathematically detectable.

3. **EventBus Integration:**
   - Subscribes to selected EventBus events via the existing `EventBus.subscribe(...)` mechanism.
   - Target event types: `secret_encrypted`, `secret_decrypted`, `secret_rotated`, `provider_failed`, `provider_recovered`, `tool_executed`, `tool_result`, `task_failed`, plus a dedicated `secret_accessed`/`secret_access_denied` pair emitted by the Secrets Manager.
   - Automatically serializes and chains these events. Filtering is configurable (an allow-list of event types), so the logger is additive and cannot break existing consumers.

4. **Non-Blocking I/O:**
   - Events are pushed onto an internal `asyncio.Queue`; a single background task drains the queue and appends to disk. The logger **never blocks the main event loop** (satisfies the "dedicated queue" requirement).

5. **Log Rotation:**
   - When the active log reaches a size threshold (default **10 MB**), it is archived as `audit_log_YYYYMMDD.jsonl.enc` — **encrypted with AES-256-GCM using the Secrets Manager master key** (via the existing `SecretsManager`) — and a fresh `audit_log.jsonl` is started.
   - `MAX_LOG_BYTES = 10 * 1024 * 1024` (configurable constant).

6. **Verification Tool:**
   - Provide a CLI script `verify_audit_log.py` that:
     - Reads every entry in `backend/audit_log.jsonl`.
     - Recomputes each entry's `hash` and checks it matches the stored `hash`.
     - Verifies each entry's `prev_hash` equals the previous entry's `hash` (first entry must match the `genesis_hash`).
     - Exits `0` (chain intact) or `1` (tampering detected, reporting the first broken index).

### Public API

```python
class AuditLogger:
    def __init__(self, log_path: str = "backend/audit_log.jsonl",
                 max_bytes: int = 10 * 1024 * 1024,
                 event_bus: EventBus | None = None,
                 secrets_manager: SecretsManager | None = None): ...
    async def start(self) -> None: ...          # subscribe + start background writer
    async def stop(self) -> None: ...           # flush + unsubscribe + stop writer
    def log(self, event: str, payload: dict) -> None: ...  # enqueue (non-blocking)
    def verify_chain(self) -> bool: ...         # integrity check (returns tamper status)
```

- `start()` subscribes the logger to the configured EventBus event types; `log()` is safe to call directly (thread/async-agnostic enqueue).
- `verify_chain()` powers the CLI tool and can be called at runtime for self-checks.

### Entry Schema (JSONL line)

```json
{
  "ts": "2026-08-04T09:30:00.123456+00:00",
  "event": "secret_decrypted",
  "payload": {"key": "groq", "caller": "orchestrator"},
  "prev_hash": "6f4b...",
  "hash": "9c2a..."
}
```

- `hash` covers a canonical serialization of `{ts, event, payload, prev_hash}` (deterministic field order, no whitespace variance) so the chain is reproducible.

## Security Considerations

- `backend/audit_log.jsonl` and `*.jsonl.enc` MUST be added to `.gitignore` (never committed).
- Archived logs are encrypted with the Secrets Manager master key (AES-256-GCM), so rotated audit history is unreadable without the master key.
- Logged payloads are **sanitized**: key names, provider names, tool names, timestamps — **never secret values** (API keys, tokens, passwords, full stdout of sensitive tools).
- The logger must never block the main event loop (async queue + background writer).
- If an event cannot be written (disk full, I/O error), the logger logs a warning and continues — it must never crash the application.

## Consequences

### Positive
- Full compliance with Principle 8 and the Level A Security Baseline.
- Tamper-evident audit trail: any post-hoc modification is detectable by `verify_audit_log.py`.
- Reuses existing infrastructure: EventBus events + Secrets Manager (for archive encryption).
- Additive component — no changes to existing consumers; backward compatible.

### Negative
- Additional disk I/O and storage growth (mitigated by rotation + encryption).
- One extra async task per process (small, bounded queue; configurable).
- Chain must be verified after crashes/restarts before trusting audit data.

### Risks
- An attacker with filesystem write access could truncate the log and rewrite the tail (only past-history tampering is fully prevented; mitigate with periodic archive encryption + off-machine backup).
- Loss of the Secrets Manager master key would make archived logs undecryptable (reuse the documented ADR-007 recovery path).

## Migration Plan

| Phase | Change | Tests Required |
|-------|--------|----------------|
| Phase 1 | `AuditLogger` core: JSONL append + SHA-256 hash chaining + `verify_chain` | New unit + workflow tests |
| Phase 2 | EventBus subscription + async queue writer (non-blocking) | Integration test with real EventBus |
| Phase 3 | Log rotation + archive encryption (Secrets Manager master key) | Rotation + encryption roundtrip tests |
| Phase 4 | `verify_audit_log.py` CLI + Secrets Manager audit events wiring | CLI acceptance test |

Each phase must pass the existing backend test suite before proceeding.

## Compliance
- [x] Backward compatibility (additive component)
- [x] Interfaces defined (AuditLogger ABC with `log` / `start` / `stop` / `verify_chain`)
- [ ] Tests (pending implementation)
- [ ] Documentation (this ADR)
- [ ] Manager approval (PENDING)

## Related Documents
- `docs/ADRs/ADR-007-secrets-manager-with-aes256-encryption.md` — Preceding ADR (Secrets Manager, emits secret audit events)
- `docs/ADRs/ADR-006-standardize-provider-rotation-and-secret-isolation.md` — Preceding ADR (provider events)
- `docs/ADRs/ADR-005-resolve-level-a-audit-contradiction.md` — Level A deliverable tracking
- `backend/moza/core/event_bus.py` — Existing EventBus (subscribe/publish mechanism)
- `backend/moza/core/models.py` — `EventType` enum (event names to subscribe to)
- `backend/moza/core/secrets_manager.py` — Master key source for archive encryption
- `backend/audit_log.jsonl` — Target audit log file (gitignored)
