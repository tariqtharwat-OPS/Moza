"""Model Performance Test Script
Tests each available LLM model with a simple prompt and measures response time and quality.
"""

import asyncio
import time
from litellm import completion
from typing import Dict, List

# List of models to test
MODELS = [
    "openrouter/qwen/qwen3-32b",
    "openai/gpt-4o",
    "groq/llama-3.3-70b-versatile",
    "anthropic/claude-sonnet-4-20260514",
    "ollama/qwen3:235b",
    "openai/qwen3-235b",
    "openai/local-model",
    "glm/glm-4",
    "sambanova/Meta-Llama-3.1-70B-Instruct",
    "gemini/gemini-2.0-flash",
    "huggingface/mistralai/Mistral-7B-Instruct-v0.3",
    "deepseek/deepseek-chat",
    "mistral/mistral-large-latest",
]

async def test_model(model: str) -> Dict[str, float | str]:
    """Test a single model with a simple prompt."""
    start_time = time.time()
    try:
        response = await completion(
            model=model,
            messages=[{"role": "user", "content": "What is the capital of France?"}]
        )
        elapsed = time.time() - start_time
        return {
            "model": model,
            "response_time": elapsed,
            "response": response.choices[0].message.content,
            "error": None
        }
    except Exception as e:
        return {
            "model": model,
            "response_time": time.time() - start_time,
            "response": None,
            "error": str(e)
        }

async def main():
    results: List[Dict[str, float | str]] = []
    for model in MODELS:
        print(f"Testing {model}...")
        result = await test_model(model)
        results.append(result)
        print(f"{model}: {result['response_time']:.2f}s")

    # Sort by response time
    results.sort(key=lambda x: x["response_time"])
    
    print("\n=== Results ===")
    for result in results:
        print(f"{result['model']}: {result['response_time']:.2f}s")
        if result["error"]:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Response: {result['response'][:100]}...")

if __name__ == "__main__":
    asyncio.run(main())