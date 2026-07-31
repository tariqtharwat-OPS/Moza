import os, requests, json, time

API_KEY = os.environ.get('GITHUB_MODELS_API_KEY', '')
BASE_URL = 'https://models.inference.ai.azure.com'

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

models = [
    ('Meta-Llama-3.1-405B-Instruct', False),
    ('Meta-Llama-3.1-8B-Instruct', False),
    ('gpt-4o', True),
    ('gpt-4o-mini', True),
]

results = []

for model_name, is_vision in models:
    print(f'\n{"="*60}')
    print(f'Testing: {model_name}')
    print(f'Vision: {is_vision}')
    print(f'{"="*60}')
    
    payload = {
        'model': model_name,
        'messages': [
            {'role': 'system', 'content': 'You are an expert Python developer. Provide complete, production-ready code.'},
            {'role': 'user', 'content': STRESS_PROMPT}
        ],
        'temperature': 0.3,
        'max_tokens': 8192,
    }
    
    start = time.time()
    try:
        resp = requests.post(
            f'{BASE_URL}/chat/completions',
            headers={'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'},
            json=payload,
            timeout=180
        )
        elapsed = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            tasks_done = 0
            checks = {
                'jwt_security': 'jwt' in content.lower() and ('expir' in content.lower() or 'token' in content.lower()),
                'nplus1': 'n+1' in content.lower() or 'eager' in content.lower() or 'selectin' in content.lower(),
                'rate_limiting': 'rate limit' in content.lower() and 'redis' in content.lower(),
                'unit_tests': 'test' in content.lower() and 'def test_' in content,
                'memory_leak': 'memory leak' in content.lower() or 'celery' in content.lower()
            }
            tasks_done = sum(checks.values())
            
            if tasks_done >= 4: quality = 'excellent'
            elif tasks_done >= 3: quality = 'good'
            elif tasks_done >= 2: quality = 'partial'
            elif tasks_done >= 1: quality = 'poor'
            else: quality = 'invalid'
            
            result = {
                'model': model_name,
                'provider': 'GitHub Models',
                'time': round(elapsed, 2),
                'status': 'success',
                'tasks_done': tasks_done,
                'quality': quality,
                'checks': checks,
                'response_length': len(content),
                'context_ok': len(content) > 3000,
                'vision': is_vision,
                'error': ''
            }
            print(f'  OK   {elapsed:.2f}s  {tasks_done}/5 tasks  {quality}  {len(content)} chars')
            
        elif resp.status_code == 429:
            print(f'  RATE LIMITED ({resp.status_code})')
            print(f'  Waiting 60s and retrying...')
            time.sleep(60)
            resp2 = requests.post(
                f'{BASE_URL}/chat/completions',
                headers={'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'},
                json=payload, timeout=180
            )
            elapsed2 = time.time() - start
            if resp2.status_code == 200:
                data2 = resp2.json()
                content2 = data2.get('choices', [{}])[0].get('message', {}).get('content', '')
                # Same evaluation...
                tasks_done2 = 0
                checks2 = {'jwt_security': 'jwt' in content2.lower() and ('expir' in content2.lower() or 'token' in content2.lower()), 'nplus1': 'n+1' in content2.lower() or 'eager' in content2.lower(), 'rate_limiting': 'rate limit' in content2.lower() and 'redis' in content2.lower(), 'unit_tests': 'test' in content2.lower() and 'def test_' in content2, 'memory_leak': 'memory leak' in content2.lower() or 'celery' in content2.lower()}
                tasks_done2 = sum(checks2.values())
                quality2 = 'excellent' if tasks_done2 >= 4 else ('good' if tasks_done2 >= 3 else ('partial' if tasks_done2 >= 2 else ('poor' if tasks_done2 >= 1 else 'invalid')))
                result = {'model': model_name, 'provider': 'GitHub Models', 'time': round(elapsed2, 2), 'status': 'success', 'tasks_done': tasks_done2, 'quality': quality2, 'checks': checks2, 'response_length': len(content2), 'context_ok': len(content2) > 3000, 'vision': is_vision, 'error': ''}
                print(f'  OK   (after retry) {elapsed2:.2f}s  {tasks_done2}/5 tasks  {quality2}')
            else:
                result = {'model': model_name, 'provider': 'GitHub Models', 'time': round(elapsed2, 2), 'status': 'failed', 'tasks_done': 0, 'quality': 'invalid', 'checks': {}, 'response_length': 0, 'context_ok': False, 'vision': is_vision, 'error': f'HTTP {resp2.status_code}: {resp2.text[:200]}'}
                print(f'  FAIL (after retry) {resp2.status_code}')
        else:
            result = {'model': model_name, 'provider': 'GitHub Models', 'time': round(elapsed, 2), 'status': 'failed', 'tasks_done': 0, 'quality': 'invalid', 'checks': {}, 'response_length': 0, 'context_ok': False, 'vision': is_vision, 'error': f'HTTP {resp.status_code}: {resp.text[:200]}'}
            print(f'  FAIL {resp.status_code}')
            print(f'  {resp.text[:200]}')
    
    except Exception as e:
        elapsed = time.time() - start
        result = {'model': model_name, 'provider': 'GitHub Models', 'time': round(elapsed, 2), 'status': 'failed', 'tasks_done': 0, 'quality': 'invalid', 'checks': {}, 'response_length': 0, 'context_ok': False, 'vision': is_vision, 'error': str(e)}
        print(f'  ERROR {elapsed:.2f}s  {e}')
    
    results.append(result)
    time.sleep(1)

# Save results
with open(r'C:\Users\eg_di\.config\opencode\github_models_stress.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f'\n{"="*60}')
print('SUMMARY')
print(f'{"="*60}')
for r in results:
    print(f'{r["model"]:30s} | {r["time"]:6.2f}s | {r["tasks_done"]}/5 | {r["quality"]:10s} | {r["status"]}')
