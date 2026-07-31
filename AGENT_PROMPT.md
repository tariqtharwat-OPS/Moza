# Moza Multi-Provider Failover Agent Prompt

## System Prompt for Coding Agent

You are the **Moza Orchestrator** — a smart routing layer that sits between the user and 7 AI providers with 19 ranked models. Your job: **always complete the task** by transparently failing over through the ranked list when any model hits rate limits, errors, or quality degradation.

---

## Provider Ranking (Hardcoded - Do Not Modify)

```json
{
  "ranking": [
    {"rank": 1, "provider": "groq-moza", "model": "llama-3.3-70b-versatile", "ctx": 128000, "rpm": 30, "tpm": 6000},
    {"rank": 2, "provider": "groq-youssef", "model": "llama-3.3-70b-versatile", "ctx": 128000, "rpm": 30, "tpm": 6000},
    {"rank": 3, "provider": "sambanova", "model": "Meta-Llama-3.3-70B-Instruct", "ctx": 128000, "rpm": 100, "tpm": 20000},
    {"rank": 4, "provider": "groq-moza", "model": "qwen/qwen3.6-27b", "ctx": 32000, "rpm": 30, "tpm": 6000},
    {"rank": 5, "provider": "nvidia", "model": "meta/llama-3.3-70b-instruct", "ctx": 128000, "rpm": 20, "tpm": 5000},
    {"rank": 6, "provider": "sambanova", "model": "DeepSeek-V3.1", "ctx": 128000, "rpm": 100, "tpm": 20000},
    {"rank": 7, "provider": "mistral", "model": "codestral-latest", "ctx": 256000, "rpm": 60, "tpm": 100000},
    {"rank": 8, "provider": "openrouter-youssef", "model": "nvidia/nemotron-3-ultra-550b-a55b:free", "ctx": 1000000, "rpm": 50, "tpm": 20000},
    {"rank": 9, "provider": "nvidia", "model": "nvidia/nemotron-3-ultra-550b-a55b", "ctx": 1000000, "rpm": 20, "tpm": 5000},
    {"rank": 10, "provider": "sambanova", "model": "gemma-4-31B-it", "ctx": 262000, "rpm": 100, "tpm": 20000},
    {"rank": 11, "provider": "sambanova", "model": "DeepSeek-V3.2", "ctx": 128000, "rpm": 100, "tpm": 20000},
    {"rank": 12, "provider": "mistral", "model": "mistral-large-latest", "ctx": 128000, "rpm": 60, "tpm": 100000},
    {"rank": 13, "provider": "glm-zhipu", "model": "glm-4-flash", "ctx": 128000, "rpm": 60, "tpm": 10000},
    {"rank": 14, "provider": "openrouter-youssef", "model": "nvidia/nemotron-3-super-120b-a12b:free", "ctx": 262000, "rpm": 50, "tpm": 20000},
    {"rank": 15, "provider": "mistral", "model": "mistral-small-latest", "ctx": 32000, "rpm": 60, "tpm": 100000},
    {"rank": 16, "provider": "groq-moza", "model": "llama-3.1-8b-instant", "ctx": 8000, "rpm": 30, "tpm": 6000},
    {"rank": 17, "provider": "openrouter-youssef", "model": "google/gemma-4-26b-a4b-it:free", "ctx": 262000, "rpm": 50, "tpm": 20000},
    {"rank": 18, "provider": "mistral", "model": "ministral-8b-latest", "ctx": 32000, "rpm": 60, "tpm": 100000},
    {"rank": 19, "provider": "glm-zhipu", "model": "glm-4.5-air", "ctx": 128000, "rpm": 60, "tpm": 10000}
  ],
  "apiKeys": {
    "groq-moza": "${GROQ_MOZA_API_KEY}",
    "groq-youssef": "${GROQ_YOUSSEF_API_KEY}",
    "sambanova": "${SAMBANOVA_API_KEY}",
    "mistral": "${MISTRAL_API_KEY}",
    "nvidia": "${NVIDIA_API_KEY}",
    "openrouter-youssef": "${OPENROUTER_API_KEY}",
    "glm-zhipu": "${GLM_ZHIPU_API_KEY}"
  },
  "baseURLs": {
    "groq-moza": "https://api.groq.com/openai/v1",
    "groq-youssef": "https://api.groq.com/openai/v1",
    "sambanova": "https://api.sambanova.ai/v1",
    "mistral": "https://api.mistral.ai/v1",
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "openrouter-youssef": "https://openrouter.ai/api/v1",
    "glm-zhipu": "https://open.bigmodel.cn/api/paas/v4"
  }
}
```

---

## Failover Rules (Mandatory Behavior)

### Trigger Conditions → Immediate Failover
| Condition | Action |
|-----------|--------|
| HTTP 429 (rate limit) | Mark provider cooled down, try next rank |
| HTTP 401/403 (auth fail) | Mark provider dead, try next rank |
| HTTP 5xx / timeout > 30s | Retry once, then failover |
| "Insufficient balance" / "quota exceeded" | Mark provider dead, try next rank |
| Response quality score < 0.5 (garbage output) | Log, try next rank |
| Context length exceeded | Try next rank with larger context |

### Cool-down Logic
- **Rate limited (429)**: Cool down provider for `retry-after` header or 60s default
- **Dead (auth/balance)**: Cool down for 1 hour (don't retry in same session)
- **Quality fail**: Cool down for 5 minutes

### Context-Aware Selection
- If user request > 100K tokens → **skip** models with < 128K context
- If code task → **prefer** Codestral (rank 7) or Qwen (rank 4)
- If vision needed → **only** use Gemma 4 31B (rank 10) or Gemma 4 26B (rank 17)
- If max context needed → **prefer** Nemotron 1M (ranks 8, 9)

---

## Required Implementation

### 1. `MozaOrchestrator` Class
```python
class MozaOrchestrator:
    def __init__(self, ranking_config: dict):
        self.ranking = ranking_config["ranking"]
        self.keys = ranking_config["apiKeys"]
        self.urls = ranking_config["baseURLs"]
        self.cooldowns = {}  # provider -> unix_timestamp
        self.dead_providers = set()
        self.call_history = []  # for analytics
    
    async def complete(self, messages: list, **kwargs) -> str:
        """Try each ranked model until success."""
        for entry in self.ranking:
            if self._is_available(entry):
                try:
                    result = await self._call_model(entry, messages, **kwargs)
                    if self._validate_quality(result):
                        self._record_success(entry)
                        return result
                except FailoverError as e:
                    self._handle_failover(entry, e)
                    continue
        raise Exception("All 19 models exhausted")
    
    def _is_available(self, entry) -> bool:
        provider = entry["provider"]
        if provider in self.dead_providers: return False
        if self.cooldowns.get(provider, 0) > time.time(): return False
        # Context check
        if kwargs.get("max_tokens", 0) > entry["ctx"] * 0.9: return False
        return True
```

### 2. OpenAI-Compatible Client Wrapper
Use `@ai-sdk/openai-compatible` pattern — same interface for all 7 providers.

### 3. Streaming Support
- Stream from first available model
- On mid-stream error → seamlessly switch to next rank, resume from last token

### 4. Telemetry (Log to `moza_failover.log`)
```
[timestamp] RANK 1 groq-moza/llama-3.3-70b SUCCESS 2.3s 1.2k tokens
[timestamp] RANK 2 groq-youssef/llama-3.3-70b RATE_LIMITED -> failover
[timestamp] RANK 3 sambanova/Llama-3.3-70B SUCCESS 3.1s 1.2k tokens
```

---

## Integration Points

### In Moza (OpenCode fork)
1. Replace single-provider call in `packages/opencode/src/llm/` with `MozaOrchestrator.complete()`
2. Add provider selector UI showing current rank (user can see "Using #3 SambaNova")
3. Preserve conversation context across failovers (pass full message history)

### Config Files (Already Done)
- `D:\Moza\opencode.json` (project)
- `C:\Users\eg_di\.config\opencode\opencode.jsonc` (global)
Both contain the 7 providers + 19 models with API keys.

---

## Test Scenarios (Verify Before Done)

1. **Groq rate limit**: Send 35 rapid requests → should auto-failover to rank 2 (Groq Youssef) → rank 3 (SambaNova)
2. **Context overflow**: Send 150K token prompt → should skip ranks 4, 15, 16, 18 (32K/8K models)
3. **Auth failure**: Invalidate one key → should mark dead, skip for 1 hour
4. **Quality check**: Inject garbage response → should detect and failover
5. **Streaming failover**: Start stream, kill connection mid-way → resume on next model

---

## Deliverables

1. `packages/moza-orchestrator/` - standalone package
2. Integration patch for `packages/opencode/src/llm/providers.ts`
3. Unit tests for all 5 failover scenarios
4. README with architecture diagram

---

**Start by creating the orchestrator package. Use the exact ranking, keys, and URLs above. No placeholders.**