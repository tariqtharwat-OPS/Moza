#!/usr/bin/env python3
"""Live ping test for top 30 high-context models from master_model_list.json"""
import json, os, sys, time, requests
from datetime import datetime

# Force UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
else:
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', buffering=1)

MASTER_LIST = r"D:\Moza\master_model_list.json"
RESULTS_FILE = r"D:\Moza\research\logs\live_test_results.json"

PROVIDER_CONFIGS = {
    "opencode-zen": {
        "base_url": "https://opencode.ai/zen/v1",
        "keys": [
            "YOUR_OPENCODE_ZEN_KEY_1",
            "YOUR_OPENCODE_ZEN_KEY_2",
            "YOUR_OPENCODE_ZEN_KEY_3"
        ],
        "model_map": {
            "deepseek-v4-flash-free": ("deepseek-ai/deepseek-v4-flash", 1000000),
            "mimo-v2.5-free": ("xiaomi/mimo-v2.5", 1000000),
            "ling-3.0-flash-free": ("inclusionai/ling-3.0-flash:free", 262144),
            "nemotron-3-ultra-free": ("nvidia/nemotron-3-ultra-550b-a55b:free", 1000000),
            "north-mini-code-free": ("cohere/north-mini-code:free", 256000),
            "laguna-s-2.1-free": ("poolside/laguna-s-2.1:free", 262144),
            "big-pickle": ("minimaxai/minimax-m3", 512000)
        }
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "keys": [
            "YOUR_GROQ_KEY_1",
            "YOUR_GROQ_KEY_2",
            "YOUR_GROQ_KEY_3"
        ]
    },
    "github": {
        "base_url": "https://models.inference.ai.azure.com",
        "keys": [
            "YOUR_GITHUB_PAT_1",
            "YOUR_GITHUB_PAT_2",
            "YOUR_GITHUB_PAT_3"
        ]
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "keys": [
            "YOUR_OPENROUTER_KEY_1",
            "YOUR_OPENROUTER_KEY_2",
            "YOUR_OPENROUTER_KEY_3"
        ]
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "keys": [
            "YOUR_MISTRAL_KEY_1",
            "YOUR_MISTRAL_KEY_2",
            "YOUR_MISTRAL_KEY_3"
        ]
    },
    "sambanova": {
        "base_url": "https://api.sambanova.ai/v1",
        "keys": [
            "YOUR_SAMBANOVA_KEY_1",
            "YOUR_SAMBANOVA_KEY_2",
            "YOUR_SAMBANOVA_KEY_3"
        ]
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "keys": [
            "YOUR_NVIDIA_KEY_1",
            "YOUR_NVIDIA_KEY_2",
            "YOUR_NVIDIA_KEY_3"
        ]
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "keys": [
            "YOUR_CEREBRAS_KEY_1",
            "YOUR_CEREBRAS_KEY_2",
            "YOUR_CEREBRAS_KEY_3"
        ]
    },
    "cloudflare": {
        "base_url": "https://api.cloudflare.com/client/v4/accounts",
        "account_ids": [
            "3f8ad0f688bd41268fbc3a1059c63b57",
            "c965aba4f56aff5dd140e32f4e6e6296",
            "0feed429c05fd38faf12e1f25c093256"
        ],
        "keys": [
            "YOUR_CLOUDFLARE_TOKEN_1",
            "YOUR_CLOUDFLARE_TOKEN_2",
            "YOUR_CLOUDFLARE_TOKEN_3"
        ]
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "keys": [
            "YOUR_ZHIPU_KEY_1",
            "YOUR_ZHIPU_KEY_2"
        ]
    }
}

PROVIDER_MODELS = {
    "opencode-zen": [
        ("deepseek-v4-flash-free", 1000000),
        ("mimo-v2.5-free", 1000000),
        ("ling-3.0-flash-free", 262144),
        ("nemotron-3-ultra-free", 1000000),
        ("north-mini-code-free", 256000),
        ("laguna-s-2.1-free", 262144),
        ("big-pickle", 512000),
    ],
    "groq": [
        ("llama-3.3-70b-versatile", 131072),
        ("llama-3.1-70b-versatile", 131072),
        ("mixtral-8x7b-32768", 32768),
        ("gemma2-9b-it", 8192),
    ],
    "github": [
        ("gpt-4o", 128000),
        ("gpt-4o-mini", 128000),
        ("Meta-Llama-3.1-405B-Instruct", 131072),
        ("Meta-Llama-3.3-70B-Instruct", 128000),
        ("Meta-Llama-3.1-8B-Instruct", 131072),
    ],
    "openrouter": [
        ("qwen/qwen3.7-flash", 1000000),
        ("nvidia/nemotron-3-ultra-550b-a55b:free", 1000000),
        ("deepseek/deepseek-v4-flash", 1000000),
        ("nvidia/nemotron-3-super-120b-a12b:free", 262144),
        ("google/gemma-4-26b-a4b-it:free", 262144),
        ("poolside/laguna-s-2.1:free", 262144),
        ("cohere/north-mini-code:free", 256000),
        ("inclusionai/ling-3.0-flash:free", 262144),
        ("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", 256000),
        ("google/gemma-4-31b-it:free", 262144),
    ],
    "mistral": [
        ("mistral-medium-2604", 262144),
        ("codestral-latest", 256000),
        ("mistral-large-latest", 262144),
        ("ministral-8b-latest", 262144),
        ("pixtral-large-latest", 128000),
    ],
    "sambanova": [
        ("Meta-Llama-3.3-70B-Instruct", 128000),
        ("gemma-4-31B-it", 262144),
        ("Meta-Llama-3.1-8B-Instruct", 131072),
        ("Meta-Llama-3.1-405B-Instruct", 131072),
    ],
    "nvidia": [
        ("deepseek-ai/deepseek-v4-flash", 1000000),
        ("deepseek-ai/deepseek-v4-pro", 1000000),
        ("minimaxai/minimax-m3", 1000000),
        ("z-ai/glm-5.2", 1000000),
        ("nvidia/nemotron-3-ultra-550b-a55b", 1000000),
        ("nvidia/nemotron-3-super-120b-a12b", 262144),
        ("moonshotai/kimi-k2.6", 262144),
        ("google/gemma-4-31b-it", 262144),
        ("thinkingmachines/inkling", 1000000),
        ("stepfun-ai/step-3.7-flash", 256000),
        ("mistralai/mistral-medium-3.5-128b", 262144),
    ],
    "cerebras": [
        ("llama-3.3-70b-instruct", 128000),
        ("llama-3.1-8b-instruct", 128000),
        ("llama-3.1-70b-instruct", 128000),
    ],
    "cloudflare": [
        ("@cf/meta/llama-3.3-70b-instruct-fp8-fast", 128000),
        ("llama-4-scout-17b-16e-instruct", 3500000),
        ("gemma-4-26b-a4b-it", 262144),
        ("glm-5.2", 1000000),
        ("gpt-oss-120b", 131072),
        ("gpt-oss-20b", 131072),
        ("kimi-k2.6", 262144),
    ],
    "zhipu": [
        ("glm-4-flash", 131072),
        ("glm-4.7-flash", 200000),
        ("glm-5.2", 1000000),
        ("glm-4-plus", 131072),
        ("glm-4-air", 131072),
        ("glm-4-airx", 131072),
        ("glm-4.7-flashx", 200000),
    ],
}

def rotate_vpn():
    """Call rotate_vpn.py to switch VPN/key context"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, r"D:\Moza\scripts\rotate_vpn.py"], capture_output=True, text=True, timeout=30)
        print(f"  VPN rotate: {result.stdout.strip()[:100]}")
        return True
    except Exception as e:
        print(f"  VPN rotate failed: {e}")
        return False

def test_model(provider, model_id, context, keys, base_url, max_retries=3):
    """Test a model with key rotation and retry logic"""
    for attempt in range(max_retries):
        key_idx = attempt % len(keys)
        api_key = keys[key_idx]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": f"Reply with exactly: OK - Context: {context}"}],
            "max_tokens": 30,
            "temperature": 0.1
        }

        # Special handling for cloudflare
        if provider == "cloudflare":
            acct_id = PROVIDER_CONFIGS["cloudflare"]["account_ids"][key_idx % 3]
            url = f"{base_url}/{acct_id}/ai/run/{model_id}"
            payload = {
                "messages": [{"role": "user", "content": f"Reply with exactly: OK - Context: {context}"}],
                "max_tokens": 30
            }
            del headers["Authorization"]
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            url = f"{base_url}/chat/completions"

        # Special: opencode-zen uses different endpoint format
        if provider == "opencode-zen":
            # Try the mapped model ID
            mapped = PROVIDER_CONFIGS["opencode-zen"]["model_map"].get(model_id)
            if mapped:
                payload["model"] = mapped[0]

        start = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            elapsed = round(time.time() - start, 2)

            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {
                    "model": model_id,
                    "provider": provider,
                    "context": context,
                    "status": "PASS",
                    "response": content.strip(),
                    "time_s": elapsed,
                    "key_index": key_idx,
                    "http_code": 200,
                    "error": None
                }
            elif resp.status_code == 429:
                print(f"  Rate limited (429) on key {key_idx}, rotating VPN...")
                rotate_vpn()
                continue
            elif resp.status_code == 402:
                return {"model": model_id, "provider": provider, "context": context,
                        "status": "FAIL", "time_s": elapsed, "http_code": 402,
                        "error": "Payment required / insufficient credits"}
            elif resp.status_code == 401:
                if attempt < max_retries - 1:
                    print(f"  401 on key {key_idx}, trying next key...")
                    continue
                return {"model": model_id, "provider": provider, "context": context,
                        "status": "FAIL", "time_s": elapsed, "http_code": 401,
                        "error": f"Unauthorized with all {len(keys)} keys"}
            elif resp.status_code == 403:
                return {"model": model_id, "provider": provider, "context": context,
                        "status": "FAIL", "time_s": elapsed, "http_code": 403,
                        "error": f"Forbidden: {resp.text[:100]}"}
            elif resp.status_code == 404:
                return {"model": model_id, "provider": provider, "context": context,
                        "status": "FAIL", "time_s": elapsed, "http_code": 404,
                        "error": f"Model not found: {resp.text[:100]}"}
            else:
                if attempt < max_retries - 1:
                    print(f"  HTTP {resp.status_code} on key {key_idx}, retrying...")
                    continue
                return {"model": model_id, "provider": provider, "context": context,
                        "status": "FAIL", "time_s": elapsed, "http_code": resp.status_code,
                        "error": resp.text[:150]}

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"  Timeout on key {key_idx}, retrying...")
                continue
            return {"model": model_id, "provider": provider, "context": context,
                    "status": "FAIL", "time_s": round(time.time() - start, 2),
                    "http_code": 0, "error": "Timeout after 30s"}
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  Error on key {key_idx}: {e}, retrying...")
                continue
            return {"model": model_id, "provider": provider, "context": context,
                    "status": "FAIL", "time_s": round(time.time() - start, 2),
                    "http_code": 0, "error": str(e)[:150]}

    return {"model": model_id, "provider": provider, "context": context,
            "status": "FAIL", "time_s": 0, "http_code": 0, "error": "Max retries exhausted"}

def main():
    print("=" * 60)
    print("LIVE PING TEST - Top High-Context Models")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    sys.stdout.flush()

    all_results = []
    total = 0
    passed = 0
    failed = 0

    for provider, models in PROVIDER_MODELS.items():
        cfg = PROVIDER_CONFIGS.get(provider, {})
        keys = cfg.get("keys", [])
        base_url = cfg.get("base_url", "")

        if not keys:
            print(f"\n  [{provider}] No keys configured, skipping")
            continue

        print(f"\n{'=' * 50}")
        print(f"  Provider: {provider.upper()} ({len(keys)} keys)")
        print(f"{'=' * 50}")

        for model_id, context in models:
            total += 1
            print(f"\n  [{total}] Testing: {model_id} ({context:,} ctx)")

            result = test_model(provider, model_id, context, keys, base_url)
            all_results.append(result)

            if result["status"] == "PASS":
                passed += 1
                print(f"  ✅ PASS ({result['time_s']}s): {result['response'][:60]}")
            else:
                failed += 1
                print(f"  ❌ FAIL ({result['http_code']}): {result['error'][:80]}")

            # Small delay between requests
            time.sleep(0.5)

    # Save results
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{round(passed/max(total,1)*100,1)}%",
        "results": all_results
    }

    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {passed}/{total} passed ({summary['pass_rate']})")
    print(f"  Saved to: {RESULTS_FILE}")
    print(f"{'=' * 60}")

    # Print table of passing models sorted by context
    passing = [r for r in all_results if r["status"] == "PASS"]
    passing.sort(key=lambda x: (-x["context"], x["time_s"]))

    if passing:
        print(f"\n  TOP PASSING MODELS:")
        print(        f"  {'Rank':<5} {'Model':<45} {'Provider':<12} {'Context':<10} {'Time':<8}")
        print(f"  {'-'*5} {'-'*45} {'-'*12} {'-'*10} {'-'*8}")
        for i, r in enumerate(passing[:15], 1):
            ctx_str = f"{r['context']/1000000:.1f}M" if r['context'] >= 1000000 else f"{r['context']//1000}K"
            print(f"  {i:<5} {r['model'][:44]:<45} {r['provider']:<12} {ctx_str:<10} {r['time_s']:<8.2f}")

    return summary

if __name__ == "__main__":
    main()
