# MISSING MODELS - Models found in research but not in API

| Model | Expected Provider | Where Found | Investigation Notes |
|-------|------------------|-------------|---------------------|
| deepseek-v4-flash-free |  | mandatory checklist | OpenCode Zen internal model. Not found in public API endpoints. May require OpenCode Zen subscription. |
| mimo-v2.5-free |  | mandatory checklist | Xiaomi MiMo v2.5 is listed on models.dev as free. OpenCode Zen may be a proxy. |
| big-pickle |  | mandatory checklist | Unclear model name. Not found in any public API or database. |
| nemotron-3-ultra-free |  | mandatory checklist | Maps to nvidia/nemotron-3-ultra-550b-a55b:free on OpenRouter. |
| laguna-s-2.1-free |  | mandatory checklist | Maps to poolside/laguna-s-2.1:free on OpenRouter. |
| north-mini-code-free |  | mandatory checklist | Maps to cohere/north-mini-code:free on OpenRouter. |
| ling-3.0-flash-free |  | mandatory checklist | Maps to inclusionai/ling-3.0-flash:free on OpenRouter. |
| qwen/qwen3-coder-plus |  | mandatory checklist | Found in OpenRouter API but not as free. Pricing: .00000065/input. |
| qwen/qwen3-coder-flash |  | mandatory checklist | Found in OpenRouter API, .000000195/input. Not free but cheap. |
| minimax/minimax-01:free |  | mandatory checklist | minimax-01 exists on OpenRouter (1M ctx, .0000002/input) but not marked as free. |
| meta-llama-3.1-405b-instruct |  | mandatory checklist | Found in GitHub API as Meta-Llama-3.1-405B-Instruct. Named differently. |
| meta-llama-3.3-70b-instruct |  | mandatory checklist | Listed on GitHub Marketplace but needs Copilot subscription. |
| mistral-large-3 |  | mandatory checklist | Not in GitHub models API response. May use different ID. |
| phi-4 |  | mandatory checklist | Not in GitHub models API response. |
| qwen/qwen3.6-27b |  | mandatory checklist | Not returned by Groq models API. May be deprecated or renamed. |
| llama-3.1-70b-versatile |  | models.dev | Listed on freellm.net but not verified via Groq API directly. |
| codestral-latest |  | mandatory checklist | Listed in Mistral docs as Premier (paid) model. |
| ministral-8b-latest |  | mandatory checklist | Latest Ministral 3 8B is Apache 2.0 licensed. |
| @cf/meta/llama-3.3-70b-instruct |  | mandatory checklist | Cloudflare uses @cf/meta/llama-3.3-70b-instruct-fp8-fast variant. |
| @cf/mistral/mistral-7b-instruct-v0.1 |  | mandatory checklist | Listed on Cloudflare but marked as deprecated. |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
