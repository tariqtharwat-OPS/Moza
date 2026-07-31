import requests
import json
import time
import os
from pathlib import Path

# Try to load .env from backend directory
_env_path = Path(__file__).resolve().parent / "backend" / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())

def _resolve(val: str) -> str:
    """Resolve ${VAR} or $VAR placeholders from environment."""
    if val.startswith("${") and val.endswith("}"):
        env_key = val[2:-1]
        return os.environ.get(env_key, val)
    if val.startswith("$"):
        return os.environ.get(val[1:], val)
    return val

HEADERS_JSON = {"Content-Type": "application/json"}

STRESS_PROMPT = """You are a senior software engineer working on a large-scale Python web application.
PROJECT CONTEXT: Flask REST API with JWT authentication, PostgreSQL database with SQLAlchemy ORM, Redis caching layer, Celery task queue for background jobs, Docker containerization, CI/CD pipeline with GitHub Actions.
CURRENT ISSUES:
1. Authentication system has security vulnerabilities - JWT tokens are not expiring properly, allowing indefinite access.
2. Database queries suffer from N+1 problem causing slow response times (5+ seconds for simple list endpoints).
3. No rate limiting on API endpoints, making the system vulnerable to abuse.
4. Missing unit tests for critical business logic (user registration, authentication, payment processing).
5. Memory leaks in background task processing causing worker crashes after 24 hours.
YOUR TASK:
1. Identify and fix ALL security vulnerabilities in the authentication system with complete code.
2. Optimize the 5 slowest database queries with proper indexing and eager loading, show before/after code.
3. Implement rate limiting (100 requests/minute per user) with Redis-based tracking.
4. Write comprehensive unit tests for user registration and login flow (minimum 10 test cases).
5. Fix the memory leak in the Celery task processor with explanation.
Provide complete, production-ready Python code for each fix. Include detailed explanations."""

def test_model(name, provider, base_url, api_key, model_id):
    url = f"{base_url}/chat/completions"
    headers = {**HEADERS_JSON, "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": STRESS_PROMPT}],
        "temperature": 0.3,
        "max_tokens": 8192,
    }
    print(f"\n{'='*60}")
    print(f"Testing: {name} ({provider})")
    print(f"Model ID: {model_id}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=180)
        elapsed = time.time() - start
        
        print(f"Status: {resp.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            length = len(content)
            print(f"Response length: {length} chars")
            
            # Quality evaluation
            tasks_done = 0
            task_keywords = [
                ("jwt", "authentication", "security"),
                ("n+1", "eager loading", "query"),
                ("rate limit", "redis"),
                ("test", "unit test", "registration"),
                ("memory leak", "celery", "worker")
            ]
            for keywords in task_keywords:
                if any(k.lower() in content.lower() for k in keywords):
                    tasks_done += 1
            
            quality = "invalid"
            if tasks_done >= 4: quality = "excellent"
            elif tasks_done >= 3: quality = "good"
            elif tasks_done >= 2: quality = "partial"
            elif tasks_done >= 1: quality = "poor"
            
            context_ok = length > 3000
            
            print(f"Tasks done: {tasks_done}/5")
            print(f"Quality: {quality}")
            print(f"Context OK: {context_ok}")
            print(f"Preview: {content[:300]}...")
            
            return {
                "model": name,
                "provider": provider,
                "model_id": model_id,
                "status_code": 200,
                "time": round(elapsed, 2),
                "length": length,
                "tasks_done": tasks_done,
                "quality": quality,
                "context_ok": context_ok,
                "error": ""
            }
        elif resp.status_code == 429:
            print(f"Rate limited! Retrying in 60s...")
            time.sleep(60)
            resp2 = requests.post(url, headers=headers, json=payload, timeout=180)
            elapsed2 = time.time() - start
            if resp2.status_code == 200:
                return test_model(name, provider, base_url, api_key, model_id)
            print(f"Still rate limited after retry")
            return {
                "model": name, "provider": provider, "model_id": model_id,
                "status_code": 429, "time": round(elapsed2, 2), "length": 0,
                "tasks_done": 0, "quality": "invalid", "context_ok": False,
                "error": "Rate limited after retry"
            }
        else:
            error = resp.text[:500]
            print(f"Error: {error}")
            return {
                "model": name, "provider": provider, "model_id": model_id,
                "status_code": resp.status_code, "time": round(elapsed, 2), "length": 0,
                "tasks_done": 0, "quality": "invalid", "context_ok": False,
                "error": error
            }
    except Exception as e:
        elapsed = time.time() - start
        print(f"Exception: {e}")
        return {
            "model": name, "provider": provider, "model_id": model_id,
            "status_code": 0, "time": round(elapsed, 2), "length": 0,
            "tasks_done": 0, "quality": "invalid", "context_ok": False,
            "error": str(e)
        }

# Test configurations
TESTS = [
    ("llama-3.3-70b-versatile", "Groq Moza", "https://api.groq.com/openai/v1", 
     "${GROQ_MOZA_API_KEY}", "llama-3.3-70b-versatile"),
    ("llama-3.3-70b-versatile", "Groq Youssef", "https://api.groq.com/openai/v1",
     "${GROQ_YOUSSEF_API_KEY}", "llama-3.3-70b-versatile"),
    ("Meta-Llama-3.3-70B-Instruct", "SambaNova", "https://api.sambanova.ai/v1",
     "${SAMBANOVA_API_KEY}", "Meta-Llama-3.3-70B-Instruct"),
    ("codestral-latest", "Mistral", "https://api.mistral.ai/v1",
     "${MISTRAL_API_KEY}", "codestral-latest"),
("DeepSeek-V3.2", "SambaNova", "https://api.sambanova.ai/v1",
      "${SAMBANOVA_API_KEY}", "DeepSeek-V3.2"),
("gemma-4-31B-it", "SambaNova", "https://api.sambanova.ai/v1",
      "${SAMBANOVA_API_KEY}", "gemma-4-31B-it"),
]

if __name__ == "__main__":
    results = []
    for name, provider, base_url, api_key, model_id in TESTS:
        resolved_key = _resolve(api_key)
        if not resolved_key or resolved_key.startswith("${"):
            print(f"WARNING: {name} ({provider}) - API key not found in environment, skipping")
            continue
        result = test_model(name, provider, base_url, resolved_key, model_id)
        results.append(result)
        time.sleep(2)  # Brief pause between tests
    
    # Save results
    with open(r"C:\Users\eg_di\.config\opencode\retest_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for r in results:
        print(f"{r['model']:30s} | {r['provider']:15s} | {r['time']:6.2f}s | {r['quality']:10s} | {r['tasks_done']}/5 | {'OK' if r['context_ok'] else 'FAIL'} | {r['status_code']}")