# ADR 001: Use LiteLLM for Multi-Provider Abstraction

**Status:** Accepted  
**Date:** 2026-01  
**Author:** Principal Engineer Team

## Context

MOZA must support 40+ LLM providers (OpenAI, Anthropic, Gemini, Azure, Ollama, local models, etc.) while maintaining a unified interface. Direct integration with each provider's SDK introduces:
- Vendor lock-in
- Duplicated boilerplate per provider
- Inconsistent error handling
- Configuration sprawl
- Difficulty swapping providers in production

## Decision

Use **LiteLLM Proxy** as the unified LLM gateway layer.

**Technical Approach:**
- LiteLLM runs as a separate service (proxy mode)
- Exposes OpenAI-compatible API at `http://localhost:4000`
- Route requests to 40+ providers via config file
- Backend communicates with LiteLLM using `litellm` Python SDK

## Consequences

### Positive
- **Single interface**: One `litellm.completion()` call works for all providers
- **Config-driven switching**: Change providers by editing `config.yaml`, no code changes
- **Built-in features**: Retry logic, fallback providers, rate limiting, cost tracking, token caching
- **Community maintained**: 30k+ GitHub stars, active development
- **Provider-agnostic**: Can swap to any LLM gateway later if needed

### Negative
- **Extra dependency**: Running separate proxy process
- **Latency overhead**: Additional network hop (minimal in practice, ~5-10ms)
- **Debugging complexity**: Must inspect both backend and LiteLLM logs

## Alternatives Considered

1. **Direct SDK integration** (rejected): Vendor lock-in, duplicated code
2. **OpenAI SDK only** (rejected): Limited to OpenAI-compatible APIs
3. **Build custom abstraction** (rejected): Reinventing wheel, maintenance burden

## Implementation

See: `backend/moza/gateway/litellm_adapter.py`

## References
- [LiteLLM Docs](https://docs.litellm.ai/)
- [OpenRouter Integration](https://docs.litellm.ai/docs/providers/openrouter)
