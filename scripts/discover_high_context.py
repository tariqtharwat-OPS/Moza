#!/usr/bin/env python3
"""
Discover High-Context Models (128K+ tokens)

This script discovers all models with context >= 128,000 tokens across all providers.
It tests each model with a simple ping request and saves the results to high_context_models.json.

Usage:
    python discover_high_context.py
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


# Provider configurations from moza_orchestrator/config.json
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_keys": {
            "Tharwat-Moza": "YOUR_GROQ_KEY_THARWAT",
            "OPS-Moza": "YOUR_GROQ_KEY_OPS",
            "Youssef-Moza": "YOUR_GROQ_KEY_YOUSSEF"
        }
    },
    "github": {
        "base_url": "https://models.inference.ai.azure.com",
        "api_keys": {
            "Tharwat-Moza": "YOUR_GITHUB_PAT_THARWAT",
            "OPS-Moza": "YOUR_GITHUB_PAT_OPS",
            "Youssef-Moza": "YOUR_GITHUB_PAT_YOUSSEF"
        }
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_keys": {
            "Tharwat-Moza": "YOUR_OPENROUTER_KEY_THARWAT",
            "OPS-Moza": "YOUR_OPENROUTER_KEY_OPS",
            "Youssef-Moza": "YOUR_OPENROUTER_KEY_YOUSSEF"
        }
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "api_keys": {
            "Tharwat-Moza": "YOUR_MISTRAL_KEY_THARWAT",
            "OPS-Moza": "YOUR_MISTRAL_KEY_OPS",
            "Youssef-Moza": "YOUR_MISTRAL_KEY_YOUSSEF"
        }
    },
    "sambanova": {
        "base_url": "https://api.sambanova.ai/v1",
        "api_keys": {
            "Tharwat-Moza": "YOUR_SAMBANOVA_KEY_THARWAT",
            "OPS-Moza": "YOUR_SAMBANOVA_KEY_OPS",
            "Youssef-Moza": "YOUR_SAMBANOVA_KEY_YOUSSEF"
        }
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_keys": {
            "Tharwat-Moza": "YOUR_NVIDIA_KEY_THARWAT",
            "OPS-Moza": "YOUR_NVIDIA_KEY_OPS",
            "Youssef-Moza": "YOUR_NVIDIA_KEY_YOUSSEF"
        }
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_keys": {
            "Tharwat-Moza": "YOUR_ZHIPU_KEY_THARWAT",
            "OPS-Moza": "YOUR_ZHIPU_KEY_OPS",
            "Youssef-Moza": None
        }
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "api_keys": {
            "Tharwat-Moza": "YOUR_CEREBRAS_KEY_THARWAT",
            "OPS-Moza": "YOUR_CEREBRAS_KEY_OPS",
            "Youssef-Moza": "YOUR_CEREBRAS_KEY_YOUSSEF"
        }
    },
    "cloudflare": {
        "base_url": "https://api.cloudflare.com/client/v4/accounts",
        "api_keys": {
            "Julia-Moza": {"account_id": "YOUR_CLOUDFLARE_ACCOUNT_ID", "token": "YOUR_CLOUDFLARE_TOKEN"},
            "OPS-Moza": {"account_id": "YOUR_CLOUDFLARE_ACCOUNT_ID_OPS", "token": "YOUR_CLOUDFLARE_TOKEN_OPS"},
            "Youssef-Moza": {"account_id": "YOUR_CLOUDFLARE_ACCOUNT_ID_YOUSSEF", "token": "YOUR_CLOUDFLARE_TOKEN_YOUSSEF"}
        }
    },
    "opencode-zen": {
        "base_url": "https://opencode.ai/zen/v1",
        "api_keys": {
            "Tharwat-Moza": "YOUR_OPENCODE_ZEN_KEY_THARWAT",
            "OPS-Moza": "YOUR_OPENCODE_ZEN_KEY_OPS",
            "Youssef-Moza": "YOUR_OPENCODE_ZEN_KEY_YOUSSEF"
        }
    }
}


# List of models to test (from config.json ranking)
MODELS_TO_TEST = [
    {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra-550b-a55b:free", "ctx": 1000000},
    {"provider": "nvidia", "model": "deepseek-ai/deepseek-v4-flash", "ctx": 1000000},
    {"provider": "nvidia", "model": "nvidia/nemotron-3-ultra-550b-a55b", "ctx": 1000000},
    {"provider": "openrouter", "model": "deepseek/deepseek-v4-flash", "ctx": 1000000},
    {"provider": "openrouter", "model": "qwen/qwen3.7-flash", "ctx": 1000000},
    {"provider": "nvidia", "model": "deepseek-ai/deepseek-v4-pro", "ctx": 1000000},
    {"provider": "nvidia", "model": "mistralai/mistral-medium-3.5-128b", "ctx": 262144},
    {"provider": "nvidia", "model": "nvidia/nemotron-3-super-120b-a12b", "ctx": 262144},
    {"provider": "nvidia", "model": "google/gemma-4-31b-it", "ctx": 262144},
    {"provider": "openrouter", "model": "poolside/laguna-s-2.1:free", "ctx": 262144},
    {"provider": "openrouter", "model": "nvidia/nemotron-3-super-120b-a12b:free", "ctx": 262144},
    {"provider": "openrouter", "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "ctx": 256000},
    {"provider": "openrouter", "model": "google/gemma-4-26b-a4b-it:free", "ctx": 262144},
    {"provider": "mistral", "model": "ministral-8b-latest", "ctx": 262144},
    {"provider": "mistral", "model": "mistral-medium-2604", "ctx": 262144},
    {"provider": "mistral", "model": "codestral-latest", "ctx": 256000},
    {"provider": "mistral", "model": "mistral-large-latest", "ctx": 262144},
    {"provider": "sambanova", "model": "Meta-Llama-3.3-70B-Instruct", "ctx": 128000},
    {"provider": "sambanova", "model": "gemma-4-31B-it", "ctx": 262144},
    {"provider": "zhipu", "model": "glm-4.7-flash", "ctx": 200000},
    {"provider": "cloudflare", "model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "ctx": 128000},
    {"provider": "cloudflare", "model": "@cf/meta/llama-4-scout-17b-16e-instruct", "ctx": 3500000},
    {"provider": "cloudflare", "model": "@cf/meta/llama-3.1-70b-instruct", "ctx": 128000},
    {"provider": "cloudflare", "model": "@cf/google/gemma-4-26b-a4b-it", "ctx": 262144},
    {"provider": "cloudflare", "model": "@cf/nvidia/nemotron-3-120b-a12b", "ctx": 256000},
    {"provider": "cloudflare", "model": "@cf/openai/gpt-oss-120b", "ctx": 131072},
    {"provider": "cloudflare", "model": "@cf/qwen/qwen3-30b-a3b-fp8", "ctx": 131072},
    {"provider": "cloudflare", "model": "@cf/zai-org/glm-4.7-flash", "ctx": 131072},
    {"provider": "opencode-zen", "model": "laguna-s-2.1-free", "ctx": 262144},
    {"provider": "opencode-zen", "model": "nemotron-3-ultra-free", "ctx": 1000000},
    {"provider": "github", "model": "gpt-4o", "ctx": 128000},
    {"provider": "github", "model": "gpt-4o-mini", "ctx": 128000},
    {"provider": "groq", "model": "llama-3.3-70b-versatile", "ctx": 128000},
    {"provider": "groq", "model": "qwen/qwen3.6-27b", "ctx": 128000},
    {"provider": "groq", "model": "llama-3.1-8b-instant", "ctx": 128000},
    {"provider": "groq", "model": "openai/gpt-oss-120b", "ctx": 128000}
]


async def list_models(provider_name: str, api_key: str, account_id: str = None) -> Optional[List[Dict[str, Any]]]:
    """List all models from a provider."""
    provider_config = PROVIDERS[provider_name]

    if provider_name == "cloudflare":
        if not account_id:
            return None
        url = f"{provider_config['base_url']}/{account_id}/ai/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
    elif provider_name == "zhipu":
        url = f"{provider_config['base_url']}/models"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
    else:
        url = f"{provider_config['base_url']}/models"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if provider_name == "cloudflare":
                    # Cloudflare returns {result: [{id, ...}, ...]}
                    models = data.get("result", [])
                else:
                    # OpenAI-compatible format
                    models = data.get("data", [])
                return models
            else:
                logger.warning(f"{provider_name} /models failed: {response.status_code} {response.text}")
                return None
    except Exception as e:
        logger.warning(f"{provider_name} /models error: {e}")
        return None


async def ping_model(provider_name: str, model_name: str, api_key: str, account_id: str = None) -> Dict[str, Any]:
    """Test a model with a simple ping request."""
    provider_config = PROVIDERS[provider_name]

    if provider_name == "cloudflare":
        if not account_id:
            return {"success": False, "error": "No account_id provided"}
        url = f"{provider_config['base_url']}/{account_id}/ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "OK"}],
            "max_tokens": 5
        }
    elif provider_name == "zhipu":
        url = f"{provider_config['base_url']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "OK"}],
            "max_tokens": 5
        }
    else:
        url = f"{provider_config['base_url']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "OK"}],
            "max_tokens": 5
        }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            start = datetime.now()
            response = await client.post(url, json=payload, headers=headers)
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {
                    "success": True,
                    "response": content[:50],
                    "elapsed": elapsed,
                    "raw_response": data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:100]}",
                    "elapsed": elapsed
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:100],
            "elapsed": 0.0
        }


async def discover_high_context_models() -> Dict[str, Any]:
    """Discover all models with context >= 128,000 tokens."""
    results = {
        "discovery_date": datetime.now().isoformat(),
        "total_providers": len(PROVIDERS),
        "total_models_tested": len(MODELS_TO_TEST),
        "high_context_models": [],
        "failed_models": [],
        "requires_normalization": []
    }

    # Test each provider to get available models
    provider_models = {}
    for provider_name, api_keys in PROVIDERS.items():
        for key_name, api_key in api_keys.items():
            if api_key is None:
                continue

            models = await list_models(provider_name, api_key)
            if models:
                provider_models[provider_name] = models
                logger.info(f"{provider_name}: Found {len(models)} models")
                break

    # Test each model
    for model_info in MODELS_TO_TEST:
        provider = model_info["provider"]
        model_name = model_info["model"]
        ctx = model_info["ctx"]

        # Check if provider has models available
        if provider not in provider_models:
            results["failed_models"].append({
                "provider": provider,
                "model": model_name,
                "ctx": ctx,
                "error": "Provider not accessible"
            })
            continue

        # Check context window
        if ctx < 128000:
            continue

        # Find the best API key to use
        api_key = None
        account_id = None

        if provider == "cloudflare":
            for key_name, key_data in PROVIDERS[provider]["api_keys"].items():
                if isinstance(key_data, dict) and "token" in key_data:
                    api_key = key_data["token"]
                    account_id = key_data["account_id"]
                    break
        else:
            for key_name, key_data in PROVIDERS[provider]["api_keys"].items():
                if isinstance(key_data, str) and key_data:
                    api_key = key_data
                    break

        if not api_key:
            results["failed_models"].append({
                "provider": provider,
                "model": model_name,
                "ctx": ctx,
                "error": "No API key available"
            })
            continue

        # Ping test the model
        logger.info(f"Testing {provider}/{model_name} (ctx={ctx:,})...")
        result = await ping_model(provider, model_name, api_key, account_id)

        if result["success"]:
            # Check for type validation errors (number instead of string)
            if isinstance(result["response"], (int, float)):
                results["requires_normalization"].append({
                    "provider": provider,
                    "model": model_name,
                    "ctx": ctx,
                    "error": "Type validation error: content is number, expected string"
                })
            else:
                results["high_context_models"].append({
                    "provider": provider,
                    "model": model_name,
                    "context_tokens": ctx,
                    "ping_response": result["response"],
                    "latency_seconds": round(result["elapsed"], 2)
                })
        else:
            results["failed_models"].append({
                "provider": provider,
                "model": model_name,
                "ctx": ctx,
                "error": result["error"]
            })

    # Sort by context window (largest first)
    results["high_context_models"].sort(key=lambda x: x["context_tokens"], reverse=True)

    return results


async def main():
    """Run the discovery."""
    logger.info("Starting high-context model discovery...")

    results = await discover_high_context_models()

    # Save results
    output_path = "D:\\Moza\\high_context_models.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n{'='*80}")
    logger.info(f"DISCOVERY COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total Providers: {results['total_providers']}")
    logger.info(f"Models Tested: {results['total_models_tested']}")
    logger.info(f"High-Context Models Found: {len(results['high_context_models'])}")
    logger.info(f"Failed Models: {len(results['failed_models'])}")
    logger.info(f"Models Requiring Normalization: {len(results['requires_normalization'])}")
    logger.info(f"{'='*80}")

    if results["high_context_models"]:
        logger.info(f"\n✓ High-Context Models (>=128K tokens):")
        for i, model in enumerate(results["high_context_models"], 1):
            logger.info(f"  {i}. {model['provider']}/{model['model']}")
            logger.info(f"     Context: {model['context_tokens']:,} tokens")
            logger.info(f"     Latency: {model['latency_seconds']}s")
            logger.info(f"     Response: {model['ping_response'][:30]}...")

    if results["requires_normalization"]:
        logger.info(f"\n⚠ Models Requiring Type Normalization:")
        for model in results["requires_normalization"]:
            logger.info(f"  - {model['provider']}/{model['model']} (ctx={model['ctx']:,})")

    if results["failed_models"]:
        logger.info(f"\n✗ Failed Models:")
        for model in results["failed_models"]:
            logger.info(f"  - {model['provider']}/{model['model']}: {model['error']}")

    logger.info(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
