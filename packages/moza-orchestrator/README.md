# Moza Orchestrator

Multi-Provider Failover Orchestrator for Moza AI System. A smart routing layer that provides transparent failover across 7 AI providers with 19 ranked models.

## Features

- **🔄 Intelligent Failover**: Automatic failover when providers hit rate limits, auth errors, or quality issues
- **🎯 Context-Aware Selection**: Chooses optimal models based on task type (code, vision, large context)
- **📊 Real-time Telemetry**: Detailed logging of all failover events and performance metrics
- **⚡ Streaming Support**: Seamless streaming with failover capability mid-stream
- **🛡️ Reliability**: Guarantees task completion through 19 ranked backup models

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Moza Orchestrator                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Provider 1    │  │   Provider 2    │  │   Provider 3    │  │
│  │   (Groq-Moza)   │  │   (Groq-Youssef) │  │  (SambaNova)    │  │
│  │   Rank #1       │  │   Rank #2       │  │   Rank #3       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                   │                   │              │
│           └───────────────────┼───────────────────┘              │
│                                 │                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Provider 4    │  │   Provider 5    │  │   Provider 6    │  │
│  │   (Groq-Qwen)   │  │   (NVIDIA)      │  │  (SambaNova)    │  │
│  │   Rank #4       │  │   Rank #5       │  │   Rank #6       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                   │                   │              │
│           └───────────────────┼───────────────────┘              │
│                                 │                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Provider 7    │  │   Provider 8    │  │   Provider 9    │  │
│  │   (Mistral)     │  │ (OpenRouter)    │  │   (NVIDIA)      │  │
│  │   Rank #7       │  │   Rank #8       │  │   Rank #9       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                 │                               │
│                                 └───────────────────────────────┘
│                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Provider 10-19 │  │   Quality Check │  │   Telemetry     │  │
│  │   (Backup)      │  │   Engine        │  │   Logger        │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         User Request                            │
└─────────────────────────────────────────────────────────────────┘
```

## Provider Ranking

The orchestrator uses a hardcoded ranking of 19 models across 7 providers:

| Rank | Provider | Model | Context | RPM | TPM |
|------|----------|-------|---------|-----|-----|
| 1 | groq-moza | llama-3.3-70b-versatile | 128K | 30 | 6K |
| 2 | groq-youssef | llama-3.3-70b-versatile | 128K | 30 | 6K |
| 3 | sambanova | Meta-Llama-3.3-70B-Instruct | 128K | 100 | 20K |
| 4 | groq-moza | qwen/qwen3.6-27b | 32K | 30 | 6K |
| 5 | nvidia | meta/llama-3.3-70b-instruct | 128K | 20 | 5K |
| 6 | sambanova | DeepSeek-V3.1 | 128K | 100 | 20K |
| 7 | mistral | codestral-latest | 256K | 60 | 100K |
| 8 | openrouter-youssef | nvidia/nemotron-3-ultra-550b-a55b:free | 1M | 50 | 20K |
| 9 | nvidia | nvidia/nemotron-3-ultra-550b-a55b | 1M | 20 | 5K |
| 10 | sambanova | gemma-4-31B-it | 262K | 100 | 20K |
| 11 | sambanova | DeepSeek-V3.2 | 128K | 100 | 20K |
| 12 | mistral | mistral-large-latest | 128K | 60 | 100K |
| 13 | glm-zhipu | glm-4-flash | 128K | 60 | 10K |
| 14 | openrouter-youssef | nvidia/nemotron-3-super-120b-a12b:free | 262K | 50 | 20K |
| 15 | mistral | mistral-small-latest | 32K | 60 | 100K |
| 16 | groq-moza | llama-3.1-8b-instant | 8K | 30 | 6K |
| 17 | openrouter-youssef | google/gemma-4-26b-a4b-it:free | 262K | 50 | 20K |
| 18 | mistral | ministral-8b-latest | 32K | 60 | 100K |
| 19 | glm-zhipu | glm-4.5-air | 128K | 60 | 10K |

## Failover Rules

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

- **Rate limited (429)**: Cool down for `retry-after` header or 60s default
- **Dead (auth/balance)**: Cool down for 1 hour (don't retry in same session)
- **Quality fail**: Cool down for 5 minutes

### Context-Aware Selection

- If user request > 100K tokens → **skip** models with < 128K context
- If code task → **prefer** Codestral (rank 7) or Qwen (rank 4)
- If vision needed → **only** use Gemma 4 31B (rank 10) or Gemma 4 26B (rank 17)
- If max context needed → **prefer** Nemotron 1M (ranks 8, 9)

## Installation

```bash
pip install moza-orchestrator
```

## Quick Start

```python
from moza_orchestrator import MozaOrchestrator

# Initialize orchestrator
orchestrator = MozaOrchestrator()

# Make a request
messages = [
    {"role": "user", "content": "Hello, can you help me with a coding task?"}
]

response = await orchestrator.complete(messages)
print(response)
```

## Advanced Usage

### Custom Configuration

```python
custom_config = {
    "ranking": [...],  # Your custom ranking
    "apiKeys": {...},  # Your API keys
    "baseURLs": {...}  # Your base URLs
}

orchestrator = MozaOrchestrator(custom_config)
```

### Streaming Requests

```python
response = await orchestrator.complete(
    messages,
    stream=True,
    temperature=0.7,
    max_tokens=1000
)
```

### Statistics and Monitoring

```python
stats = orchestrator.get_stats()
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Dead providers: {stats['dead_providers']}")
```

## Testing

Run the test suite to verify all failover scenarios:

```bash
pytest tests/
```

### Test Scenarios

1. **Groq rate limit**: Send 35 rapid requests → auto-failover to rank 2 → rank 3
2. **Context overflow**: Send 150K token prompt → skip small context models
3. **Auth failure**: Invalidate one key → mark dead, skip for 1 hour
4. **Quality check**: Inject garbage response → detect and failover
5. **Streaming failover**: Start stream, kill connection mid-way → resume on next model

## Telemetry

All failover events are logged to `moza_failover.log` with format:

```
[timestamp] RANK 1 groq-moza/llama-3.3-70b SUCCESS 2.3s 1.2k tokens
[timestamp] RANK 2 groq-youssef/llama-3.3-70b RATE_LIMITED -> failover
[timestamp] RANK 3 sambanova/Llama-3.3-70B SUCCESS 3.1s 1.2k tokens
```

## Integration with Moza

To integrate with the existing Moza system:

1. Replace single-provider calls in `packages/opencode/src/llm/` with `MozaOrchestrator.complete()`
2. Add provider selector UI showing current rank
3. Preserve conversation context across failovers

## API Reference

### MozaOrchestrator

#### `__init__(ranking_config=None)`
Initialize the orchestrator with optional custom configuration.

#### `async complete(messages, **kwargs)`
Complete a request through the ranked providers.

**Parameters:**
- `messages`: List of message dictionaries
- `temperature`: Temperature for generation (default: 0.7)
- `max_tokens`: Maximum tokens to generate
- `stream`: Whether to stream the response
- `timeout`: Request timeout in seconds

**Returns:**
- Generated response content

#### `get_stats()`
Get performance statistics.

**Returns:**
- Dictionary with success rate, dead providers, cooldown info

### FailoverError

Exception raised when failover is triggered.

**Attributes:**
- `provider`: Provider name
- `model`: Model name
- `error_type`: Type of error (rate_limit, auth_error, etc.)
- `message`: Error message

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: https://github.com/moza-ai/moza-orchestrator/issues
- Documentation: https://moza-ai.github.io/moza-orchestrator/