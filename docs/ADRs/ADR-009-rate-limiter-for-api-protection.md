# ADR-009: Rate Limiter for API Protection

## Status: Proposed

## Context
The Moza system currently has functional Gateway, Secrets Manager, and Audit Logger. However, without rate limiting, a single user or script could exhaust API quotas or crash the server, leading to denial of service or degraded performance.

## Decision
Implement a **Token Bucket** algorithm as FastAPI middleware to protect API endpoints from abuse. This will ensure fair usage and prevent resource exhaustion.

## Key Features
- **Per-IP rate limiting**: Default limit of 60 requests per minute.
- **Per-User/Session rate limiting**: If authenticated, apply stricter limits.
- **Configurable limits**: Define limits in `constitution.yaml` or `.env`.
- **HTTP 429 Response**: Return `429 Too Many Requests` with `Retry-After` header when limits are exceeded.
- **Audit Logging**: Log rate limit violations to the Audit Logger.

## Implementation Details
- **Algorithm**: Token Bucket for simplicity and effectiveness.
- **Middleware**: FastAPI middleware to intercept requests and enforce limits.
- **Exemptions**: Health check endpoints (`/health`) should not be rate-limited.

## Backward Compatibility
- No breaking changes to existing APIs.
- Existing configurations remain unaffected.

## Open Questions
- Should per-user limits be configurable per role?
- How to handle bursty traffic spikes?

## References
- [FastAPI Rate Limiting Guide](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)

---