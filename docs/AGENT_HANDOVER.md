# AGENT HANDOVER — Moza Project Status

> **Generated:** 2026-07-31  
> **Last commit:** `119cca7` — `feat(gateway): complete ADR-006 Phase 5 - formal circuit breaker and rate-limit key cycling with workflow test`  
> **Branch:** `main`  
> **Remote:** `origin` (`https://github.com/tariqtharwat-OPS/Moza.git`)

---

## Completed Work (ADR-006 — 5 Phases)

### Phase 1 — Env-Only Secret Loading
- Env var checked first (`ENV_KEY_MAP` covers all 10 providers), config.json fallback.
- Logs key source (env vs config.json). Warning when no key found.
- config.json key loading still present (deferred removal to planned env-only mode).

### Phase 2 — Provider Ranking Consolidation
- Duplicate `provider_ranking` sections in `constitution.yaml` consolidated into one.
- All 26 providers preserved in original order; YAML validity verified.
- Comment added referencing config.json as the live operational source.

### Phase 3 — Unified Health Tracking
- `HealthTracker` is the master source of truth for cooldowns.
- `MozaOrchestrator` accepts injected `health_tracker`; `cooldowns` is now a read-only `@property` proxying to the tracker.
- `LLMRouter` shares its `HealthTracker` (wired to EventBus) with orchestrator.
- `provider_failed` / `provider_recovered` events published on cooldown transitions.
- Backward compatible: local cooldown fallback kept when no tracker provided.
- 13 unit tests in `test_health_sync.py`.

### Phase 4 — VPN Rotation with Confirmation
- `SCRIPTS_DIR` fixed (now walks to repo root `D:\Moza\scripts`, finds `ROTATE_VPN_SCRIPT`).
- `_get_public_ip()` fetches IP via `api.ipify.org` (5s timeout).
- `_wait_for_ip_change()` polls every 3s up to 30s for IP change after VPN rotation.
- `_maybe_rotate_vpn()` returns `bool`: True on IP change or unverifiable (optimistic + 5s delay), False on timeout.
- 13 unit tests in `test_vpn_rotation.py` (FakeResponse + FakeClock pattern).
- 110 unit tests pass.

### Phase 5 — Formal Circuit Breaker + Rate Limit Key Cycling (THIS HANDOVER)

#### Files Modified
| File | Change |
|------|--------|
| `backend/moza/gateway/health_tracker.py` | Added `CircuitState` enum, `CIRCUIT_FAILURE_THRESHOLD=3`, `CIRCUIT_OPEN_TIMEOUT=30`. Added circuit fields to `ProviderHealth`. Added `get_circuit_state()`, `record_circuit_failure()`, `allows_request()`, `is_circuit_open()`. Circuit-aware `is_on_cooldown()` (OPEN blocks, HALF_OPEN allows probe). `reset()` preserves circuit state. `_apply_cooldown`/`record_success` integrate circuit. |
| `packages/moza-orchestrator/src/moza_orchestrator/orchestrator.py` | Added `_rate_limited_keys` per-provider tracker. Added `_handle_rate_limit_cycle()` for cycling to non-rate-limited keys on 429. Added `_try_with_key_retry()` wrapper that retries same entry on 429 key cycling within a single request. Added `_record_circuit_failure()` helper. `_record_success()` resets `_rate_limited_keys`. |
| `backend/tests/integration/test_circuit_breaker_workflow.py` | Smart workflow test: Provider A (3 keys) all 429 → circuit OPEN → fallback Provider B → 200 → after 30s HALF_OPEN probe → 200 → CLOSED. Asserts EventBus events. |
| `docs/ADRs/ADR-006-standardize-provider-rotation-and-secret-isolation.md` | Phase 5 checkbox `[x]`, migration table updated, test references updated. |

#### Circuit Breaker States
- **CLOSED**: normal operation; 3 consecutive same-type failures → OPEN.
- **OPEN**: blocks all requests (`is_on_cooldown` returns True); after 30s → HALF_OPEN (lazy transition).
- **HALF_OPEN**: allows one probe request (even if a cooldown deadline is active); 1 success → CLOSED (publishes `provider_recovered`); 1 failure → OPEN (re-starts 30s timer).

#### 429 Key Cycling Flow
1. `_try_with_key_retry()` calls `_try_call(entry)`. On FailoverError rate_limit:
2. `_handle_rate_limit_cycle()`: marks current key as rate-limited in `_rate_limited_keys[provider]`.
3. If a non-rate-limited key exists: `record_circuit_failure(defer_open=True)` (counts toward threshold but keeps circuit closed), cycles to next key, returns True → retry.
4. If all keys rate-limited: returns False → `_try_with_key_retry` re-raises → caller's `_handle_failover` applies cooldown (circuit opens at threshold via `_apply_cooldown` → `_count_circuit_failure`).

#### Architecture Notes
- `_clear_provider_cooldowns()`/`reset()` at start of every `complete_with_tools()` preserves circuit state (only clears cooldowns + legacy consecutive_failures). This allows circuit to persist across user requests.
- `apply_cooldown` suppresses its own `provider_failed` event when `_count_circuit_failure` just opened the circuit (avoids duplicate event).
- `_try_with_key_retry` is used for both smart entry and fallback chain entries.
- `is_on_cooldown(provider)`: OPEN → True, HALF_OPEN → False (allows probe), CLOSED → cooldown_until check.

#### Deferred / Open Items
- `backend/constitution.yaml` still carries its own separate 19-entry `provider_ranking` (only consumer: `router.py` summary fallback). Deferred from Phase 2, flagged in Phase 4 status.
- `constitution.yaml.bak` exists in repo root from Phase 2 — remove if no longer needed.
- `test_e2e_flow.py::TestSSEStream::test_sse_event_order` appears flaky (SSE event ordering not related to ADR-006).
- config.json key loading still present (env-only mode deferred to future).

---

## Test Results

```
$ python -m pytest tests/unit -q
110 passed in 4.83s

$ python -m pytest tests/integration/test_circuit_breaker_workflow.py -v
1 passed in 0.36s

$ python -m pytest tests/unit tests/integration -q
128 passed, 1 failed (test_sse_event_order - pre-existing flaky)
```

---

## How to Run Tests

```powershell
$env:TEMP="C:\Users\eg_di\AppData\Local\Temp\opencode"
cd backend
python -m pytest tests/unit -q
python -m pytest tests/integration -v
```

---
 
## Git Log
 
```
5481e86  fix: update MozaLauncher to start backend on port 8001 to match frontend expectations
119cca7  feat(gateway): complete ADR-006 Phase 5 - formal circuit breaker and rate-limit key cycling with workflow test
ab4d691  feat(gateway): implement Phase 4 of ADR-006 - VPN rotation with IP confirmation
... (earlier commits)
```
 
---
 
## Key Files Reference
 
| File | Purpose |
|------|---------|
| `D:\Moza\MozaLauncher.exe` | **CRITICAL: Always use this to start the system.** Starts backend on port 8001, frontend on 3000, opens Chrome. |
| `backend/moza/gateway/health_tracker.py` | Health tracking + circuit breaker implementation |
| `packages/moza-orchestrator/src/moza_orchestrator/orchestrator.py` | Orchestrator with failover + key cycling |
| `backend/moza/gateway/router.py` | Router wiring HealthTracker → Orchestrator |
| `backend/moza/core/event_bus.py` | EventBus (SYSTEM_SESSION, publish_nowait) |
| `backend/moza/core/models.py` | EventType (PROVIDER_FAILED, PROVIDER_RECOVERED) |
| `backend/tests/unit/test_health_sync.py` | Health sync unit tests (fixture patterns) |
| `backend/tests/unit/test_vpn_rotation.py` | VPN rotation unit tests (FakeClock pattern) |
| `backend/tests/integration/test_circuit_breaker_workflow.py` | Phase 5 workflow integration test |
| `docs/ADRs/ADR-006-standardize-provider-rotation-and-secret-isolation.md` | ADR-006 status and specs |