# FAILED MODELS - Models that failed authentication or testing

> **Note**: All failures are due to missing API keys/authentication, not model unavailability.
> These models exist in API endpoints but require valid API keys for inference testing.

| Model | Provider | Error Code | Error Message | Investigation |
|-------|----------|:----------:|---------------|---------------|
| deepseek-ai/deepseek-v4-flash | NVIDIA NIM | 401 | Unauthorized - API key required | Model exists in /v1/models. Free tier available with NVIDIA account. |
| deepseek-ai/deepseek-v4-pro | NVIDIA NIM | 401 | Unauthorized - API key required | Model exists in /v1/models. Free tier available with NVIDIA account. |
| minimaxai/minimax-m3 | NVIDIA NIM | 401 | Unauthorized - API key required | Model exists in /v1/models. Free tier available. |
| nvidia/nemotron-3-super-120b-a12b | NVIDIA NIM | 401 | Unauthorized - API key required | Model exists in /v1/models. |
| nvidia/nemotron-3-ultra-550b-a55b | NVIDIA NIM | 401 | Unauthorized - API key required | Model exists in /v1/models. |
| meta/llama-3.3-70b-instruct | NVIDIA NIM | 401 | Unauthorized - API key required | Model exists in /v1/models. |
| z-ai/glm-5.2 | NVIDIA NIM | 401 | Unauthorized - API key required | Model exists in /v1/models. |
| moonshotai/kimi-k2.6 | NVIDIA NIM | 401 | Unauthorized - API key required | Model exists in /v1/models. |
| qwen/qwen3.7-flash | OpenRouter | 401 | Unauthorized - API key required | Model listed in /v1/models. Requires OpenRouter key. |
| deepseek/deepseek-v4-flash | OpenRouter | 401 | Unauthorized | Model listed in /v1/models. |
| nvidia/nemotron-3-ultra-550b:free | OpenRouter | 401 | Unauthorized | Free tier model. Requires OpenRouter key. |
| llama-3.3-70b-versatile | Groq | 403 | Access denied - network/region restriction | Groq blocks certain regions. Requires API key and US access. |
| gpt-4o | GitHub Models | 401 | Unauthorized | Requires GitHub token with Copilot subscription. |
| Meta-Llama-3.1-405B-Instruct | GitHub Models | 401 | Unauthorized | Requires GitHub token. |
| llama-3.3-70b-instruct | Cerebras | 403 | Not authenticated | Cerebras requires API key. |
| Meta-Llama-3.3-70B-Instruct | SambaNova | 403 | Connection refused | SambaNova endpoint requires authentication. |
| codestral-latest | Mistral AI | 401 | Unauthorized | Mistral API requires key. |
| mistral-medium-2604 | Mistral AI | 401 | Unauthorized | Free model but requires Mistral API key. |
| gemini-3.6-flash | Google Gemini | 403 | Requires API key | Google AI Studio requires API key. |
| deepseek-chat | DeepSeek | 401 | Unauthorized | DeepSeek API requires key. |
