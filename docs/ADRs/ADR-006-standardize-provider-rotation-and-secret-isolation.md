# ADR-006: Standardize Provider Rotation and Secret Isolation Strategy

## Status
**Proposed**

## Date
2026-07-31

## Context

The current LLM Gateway has a 3-tier fallback architecture (Key Rotation → Provider Failover → VPN Rotation) implemented across `orchestrator.py`, `gateway/router.py`, and `scripts/rotate_vpn.py`. A READ-ONLY analysis conducted on 2026-07-31 revealed 6 critical gaps:

1. **SECRET ISOLATION VIOLATION (Principle 12.5):** Keys load from `config.json` (in repo) first, then env vars override. This exposes secrets in version control and violates the Level A Security Baseline requirement that all secrets must be stored outside source code.

2. **DUPLICATE SSOT:** `constitution.yaml` has duplicate provider ranking sections (lines 75 and 79) with overlapping but differently-named provider entries (e.g., `"groq"` in config.json vs `"groq-moza"` in constitution.yaml).

3. **DUPLICATE HEALTH TRACKING:** `HealthTracker` (gateway layer at `gateway/health_tracker.py`) and `MozaOrchestrator.cooldowns` (package at `orchestrator.py:147-150`) are independent with no synchronization between them.

4. **VPN FIRE-AND-FORGET:** `_maybe_rotate_vpn()` (`orchestrator.py:225-239`) uses `subprocess.Popen` without waiting for IP change confirmation before retries, meaning retries may use the same blocked IP.

5. **RATE LIMIT GAP:** Rate limit errors (429) trigger cooldown but NOT key cycling — only `auth_error` and `dead` trigger key rotation (`orchestrator.py:209-213`).

6. **NO FORMAL CIRCUIT BREAKER:** Only cooldowns/block lists exist; no open/closed/half-open state machine as required by Level A Section 14.1.

## Decision

Implement a unified `RotationManager` component addressing all 6 gaps through 5 implementation phases:

### Phase 1 — Env-Only Secret Loading (Priority 1)

- Remove `config.json` as a key source entirely
- Load ALL secrets from environment variables only (sourced from `backend/.env`)
- Add startup validation: fail fast if required keys are missing
- Retain `config.json` only for non-secret configuration (ranking, routing rules, timeouts)
- *This is a BREAKING CHANGE requiring the migration plan below*

### Phase 2 — Provider Ranking Consolidation

- Remove the duplicate ranking section from `constitution.yaml` (lines 75-78)
- Keep `config.json > ranking` as the single authoritative ranking list
- Update `constitution.yaml` to reference `config.json` as the ranking source

### Phase 3 — Unified Health Tracking

- Promote `HealthTracker` from gateway layer to shared `moza/core/` module
- Single `HealthTracker` instance shared between gateway and orchestrator
- Synchronize cooldowns across both layers via EventBus events
- Cooldown events: `provider_cooldown_started`, `provider_cooldown_ended`

### Phase 4 — VPN Rotation with Confirmation

- Replace fire-and-forget `subprocess.Popen` with async subprocess + IP verification loop
- Wait for confirmed IP change (verified via `api.ipify.org`) before retrying providers
- Add 30-second timeout with fallback to next provider if VPN rotation fails
- Log VPN rotation attempts and outcomes to audit trail

### Phase 5 — Formal Circuit Breaker + Rate Limit Key Cycling

- Implement circuit breaker states (closed/half-open/open) per provider
- Thresholds: 3 consecutive failures → open; 30s → half-open; 1 success → closed
- Extend key rotation trigger to include 429 (rate limit) errors
- Add per-key rate limit counters to distribute load across keys
- Integrate with existing cooldown mechanism (additive, not replacement)

### Migration Plan

| Phase | Duration | Change | Tests Required |
|-------|----------|--------|----------------|
| Phase 1 | 1 day | Dual-read: env first, config.json fallback with deprecation warning | 94+ existing + benchmark |
| Phase 2 | 1 day | Add env-only mode flag; remove config.json key loading | 94+ existing + benchmark |
| Phase 3 | 1 day | Consolidate rankings; deduplicate constitution.yaml | 94+ existing + benchmark |
| Phase 4 | 1–2 days | Merge health tracking; add EventBus sync | 94+ existing + benchmark + new integration tests |
| Phase 5 | 1–2 days | Circuit breaker; rate limit key cycling | 110+ existing + new integration test |

Each phase must pass all 94+ existing tests and 5 frozen benchmarks before proceeding.

## Consequences

### Positive
- Full compliance with Principle 12.5 (Secret Isolation — all secrets outside source code)
- Eliminates duplicate health tracking confusion
- More robust fallback with VPN IP confirmation
- Formal Circuit Breaker satisfies Level A deliverable (Section 14.1)
- Rate limit handling improves provider utilization via key cycling
- Single source of truth for provider ranking

### Negative
- **Breaking change** for any code that reads API keys from `config.json`
- Migration period (estimated 5–8 days across all 5 phases)
- Increased complexity in gateway layer (new `RotationManager` component)
- VPN confirmation adds ~3–30s latency to failover scenarios

### Risks
- If migration is rushed, existing provider connections may break (mitigated by phased approach)
- VPN confirmation timeout (30s) could cause user-perceived delay (mitigated by concurrent failover to next provider)
- Circuit breaker thresholds may need tuning per provider (mitigated by configurable thresholds in Phase 5)

## Compliance
- [x] Backward compatibility addressed (3-phase migration with deprecation warnings)
- [x] Migration plan included (breaking change — 5 phases)
- [x] Interfaces updated (new `RotationManager` interface in Phase 3)
- [x] Tests updated (Phase 1: 8 secret-loading tests in `test_secret_loading.py`; Phase 3: 13 health-sync tests in `test_health_sync.py`; Phase 4: 13 VPN rotation tests in `test_vpn_rotation.py`; Phase 5: 1 circuit breaker workflow test in `test_circuit_breaker_workflow.py`)
- [x] Documentation updated (this ADR + constitution.yaml cleanup in Phase 2)
- [ ] Manager approval obtained (PENDING)

## Phase 1 Status (2026-07-31)
- [x] Env var checked first, config.json as fallback (env takes precedence)
- [x] `ENV_KEY_MAP` expanded to cover all 10 providers in config.json apiKeys
- [x] Log source used (environment vs config.json) and warn when no key found
- [ ] Remove config.json key loading entirely (planned for Phase 2, per migration table above)

## Phase 2 Status (2026-07-31)
- [x] Duplicate provider-ranking sections in `constitution.yaml` (lines 75 and 79) consolidated
- [x] All 26 providers preserved in original order (no ranking changes, backward compatible)
- [x] YAML validity verified (parsed via `moza.core.constitution.load_constitution`)

### Migration Note — Phase 2
- **Sections identified:** the root `constitution.yaml` contained two duplicate header blocks before `provider_ranking:` — one dated "real stress test results (2026-07-29)" and one dated "live OpenRouter discovery (2026-07-29)".
- **Section kept as SSOT:** the `provider_ranking` list itself (26 entries). It already contains every provider referenced by both header blocks (stress-tested `github-models/gpt-4o` from the older block; `qwen3.7-flash`, `qwen3-coder-plus`, `qwen3-coder-flash`, `laguna-s-2.1:free`, `nemotron-nano-omni:free` from the newer block). Both blocks described the same single list, so no provider merge was required — the list was already fully consolidated.
- **Removed:** the duplicate second header block; the two headers were merged into one.
- **Comment added:** `# SSOT: Consolidated from duplicate sections per ADR-006 Phase 2` plus a reference to `config.json > ranking` as the live operational source.
- **Backup:** `constitution.yaml.bak` created in repo root for rollback.
- **No code changes required:** the removed section was comments only; all consumers (`moza.core.constitution.get_constitution`, `gateway/router.py` summary fallback) still read the `provider_ranking` key, which is unchanged.
- **Open follow-up (deferred to Phase 4):** `backend/constitution.yaml` still carries its own separate 19-entry `provider_ranking`. Its only consumer is the `router.py` summary fallback (used only when no calls recorded yet). Consolidating it onto the root file is now **scheduled for Phase 4** (see Phase 4 Status below).

## Phase 3 Status (2026-07-31)
- [x] `HealthTracker` is now the master source of truth for provider cooldowns
- [x] `MozaOrchestrator` accepts an injected `health_tracker`; its `cooldowns` dict became a read-only `@property` that proxies to the tracker (local fallback kept for standalone use)
- [x] `HealthTracker` publishes `provider_failed` / `provider_recovered` events to the EventBus on cooldown state transitions
- [x] New `EventType` values (`provider_failed`, `provider_recovered`) and `EventBus.SYSTEM_SESSION` + `publish_nowait` (sync publish for non-async producers)
- [x] `LLMRouter` now shares its `HealthTracker` (wired to the EventBus) with `MozaOrchestrator`
- [x] Backward compatible: legacy 3-strike `record_failure(provider, model)` behaviour preserved; orchestrator without a tracker uses its local cooldown dict
- [x] 13 new unit tests in `backend/tests/unit/test_health_sync.py` (event-driven sync, proxy property, backward compat)

### Migration Note — Phase 3
- **Unification strategy:** cooldown state is owned solely by `HealthTracker`. The orchestrator queries it directly (`is_on_cooldown`, `get_cooldowns`) rather than maintaining a parallel dict — synchronous querying avoids event-loop race conditions, while the tracker still emits events on the EventBus so any layer can react. `orchestrator.cooldowns` remains a read-only property for external readers.
- **Event contract:** `provider_failed` (payload: provider, model, error_type, cooldown_until) on cooldown entry; `provider_recovered` (payload: provider, model, latency) when a success clears an active cooldown. Both use `EventBus.SYSTEM_SESSION = "__system__"`.
- **Failover behaviour preserved:** error-type cooldown durations (rate_limit 60s, auth_error 3600s, ip_blocked 300s, etc.), key-cycling on auth errors, `dead_providers`, and `blocked_providers` (VPN rotation trigger) all unchanged — only the storage of cooldown deadlines moved.

## Phase 4 Status (2026-07-31)
- [x] VPN rotation with IP-change confirmation (from migration table)
- [ ] **Deferred from Phase 2:** consolidate `backend/constitution.yaml`'s separate 19-entry `provider_ranking` onto the root `constitution.yaml` (flagged for cleanup here; only consumer is the `router.py` summary fallback)

## Phase 5 Status (2026-07-31)
- [x] Formal Circuit Breaker states (CLOSED/OPEN/HALF_OPEN) implemented in `HealthTracker` (`backend/moza/gateway/health_tracker.py`)
- [x] Thresholds: 3 consecutive same-type failures → OPEN; 30s → HALF_OPEN (lazy transition in `get_circuit_state`); 1 success → CLOSED
- [x] Circuit breaker integrated with existing cooldown mechanism (additive — cooldowns persist independently; HALF_OPEN overrides cooldown to allow the recovery probe)
- [x] 429 (rate limit) now triggers key cycling: `_handle_rate_limit_cycle` cycles to a non-rate-limited key and retries without tripping the breaker or applying a cooldown; cooldown + circuit breaker only apply when ALL keys fail with 429
- [x] Per-key rate limit counters (`_rate_limited_keys` dict in orchestrator) track which keys have hit 429 in the current rotation cycle, preventing immediate re-use of a rate-limited key
- [x] `_try_with_key_retry` wraps every provider entry call; it handles retry-with-next-key within a single request instead of deferring to the next request
- [x] `HealthTracker` never records a failure without the circuit breaker knowing about it (every `_apply_cooldown` and `record_circuit_failure` feeds the same state machine)
- [x] Existing failover logic preserved: auth_error/dead still cycle via `_cycle_provider_key` (without in-request retry); ip_blocked, server_error, timeout, etc. still apply immediate cooldown
- [x] Backward compatible: 110 unit tests pass unchanged; single-key providers behave identically to Pre-Phase-5 (429 → 60s cooldown)
- [x] Smart workflow test: `backend/tests/integration/test_circuit_breaker_workflow.py` — Provider A (3 keys) all 429 → circuit OPEN → route to Provider B → 200 OK → after 30s HALF_OPEN probe → 200 → CLOSED; asserts EventBus emits `provider_failed` (with circuit_state="open") and `provider_recovered` at correct times
- [x] Circuit breaker state intentionally preserved across `_clear_provider_cooldowns`/`reset()` — an OPEN circuit survives between user requests so the 30s → HALF_OPEN → probe flow works

## Impact Analysis

| Component | Change Type | Risk |
|-----------|-------------|------|
| `packages/moza-orchestrator/src/moza_orchestrator/orchestrator.py` | Refactor key loading, cooldown, VPN calls | Medium |
| `backend/moza/gateway/router.py` | Integrate shared HealthTracker | Low |
| `backend/moza/gateway/health_tracker.py` | Promote to moza/core/; add EventBus sync | Low |
| `constitution.yaml` | Remove duplicate ranking section | Low |
| `packages/moza-orchestrator/config.json` | Deprecate key storage; retain ranking/routing | Medium |
| `scripts/rotate_vpn.py` | Add async IP confirmation loop | Low |
| `backend/.env` | Add required env var schema | Low |

**Frozen benchmarks at risk:** NONE — all Phase 1–3 changes are additive with deprecation warnings; Phase 4–5 add new behavior without removing existing paths.

## Related Documents
- `docs/MOZA_MASTER_PLAN.md` Section 14.1 — Level A Key Deliverables (Circuit Breaker)
- `docs/MOZA_MASTER_PLAN.md` Section 12.5 — Level A Security Baseline (Secret Isolation)
- `docs/MOZA_MASTER_PLAN.md` Principle 14 — LLM is a replaceable CPU
- `docs/ADRs/ADR-005-resolve-level-a-audit-contradiction.md` — Preceding ADR on Level A completeness
- `packages/moza-orchestrator/src/moza_orchestrator/orchestrator.py` — Current orchestrator implementation
- `backend/moza/gateway/health_tracker.py` — Current health tracker
- `backend/moza/gateway/router.py` — Current gateway router
- `scripts/rotate_vpn.py` — Current VPN rotation script
- `constitution.yaml` — Constitution with duplicate rankings to be resolved
