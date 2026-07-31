import json

# Load all previous test results
with open(r'C:\Users\eg_di\.config\opencode\stress_results.json') as f:
    stress = json.load(f)

with open(r'C:\Users\eg_di\.config\opencode\retest_results.json') as f:
    retest = json.load(f)

# Model context sizes (in tokens)
CTX = {
    'llama-3.1-8b-instant': 8000,
    'llama-3.3-70b-versatile': 128000,
    'qwen/qwen3.6-27b': 32000,
    'Meta-Llama-3.3-70B-Instruct': 128000,
    'DeepSeek-V3.1': 128000,
    'DeepSeek-V3.2': 128000,
    'gemma-4-31B-it': 262000,
    'codestral-latest': 256000,
    'mistral-small-latest': 32000,
    'mistral-large-latest': 128000,
    'ministral-8b-latest': 32000,
    'meta/llama-3.3-70b-instruct': 128000,
    'nvidia/nemotron-3-ultra-550b-a55b': 1000000,
    'nvidia/nemotron-3-super-120b-a12b:free': 262000,
    'google/gemma-4-26b-a4b-it:free': 262000,
    'glm-4-flash': 128000,
    'glm-4.5-air': 128000,
    'gemini-2.0-flash': 1000000,
    'gemini-2.5-flash': 1000000,
    'deepseek-v4-flash': 128000,
    'deepseek-v4-pro': 128000,
    'deepseek-ai/deepseek-v4-flash': 128000,
    'mistralai/mistral-large-2-instruct': 128000,
    'cohere/north-mini-code:free': 32000,
    'poolside/laguna-s-2.1:free': 32000,
    'google/gemma-4-31b-it:free': 262000,
}

QUAL = {'excellent': 100, 'good': 75, 'poor': 50, 'partial': 25, 'invalid': 0}

# Merge results - use best result for each model
best = {}
for r in stress + retest:
    key = r.get('model') or r.get('Model')
    status = r.get('status_code', r.get('Status', ''))
    if key not in best or (status == 200 and best[key].get('status_code', best[key].get('Status', '')) != 200):
        best[key] = r

# Score each model
scored = []
for m in best.values():
    model = m.get('model') or m.get('Model')
    provider = m.get('provider') or m.get('Provider')
    time = m.get('time') or m.get('Time', 0)
    quality = m.get('quality') or m.get('Quality', 'invalid')
    tasks = m.get('tasks_done') or m.get('TasksDone', 0)
    ctx_ok = m.get('context_ok') or m.get('ContextOk', False)
    error = m.get('error') or m.get('Error', '')
    status_code = m.get('status_code') or m.get('Status', 0)
    
    ctx = CTX.get(model, 0)
    
    s = 100 if status_code == 200 else 0
    sp = max(0, (120 - time) / 120 * 100)
    q = QUAL.get(quality, 0)
    c = 100 if ctx_ok and ctx >= 4000 else (50 if ctx_ok else 0)
    
    total = s * 0.40 + sp * 0.25 + q * 0.25 + c * 0.10
    
    scored.append({
        'model': model,
        'provider': provider,
        'time': time,
        'status': 'success' if status_code == 200 else 'failed',
        'tasks_done': tasks,
        'quality': quality,
        'ctx': ctx,
        'context_ok': ctx_ok,
        'error': error,
        'score': total,
        'components': {'success': s, 'speed': sp, 'quality': q, 'context': c}
    })

# Sort by score descending
scored.sort(key=lambda x: x['score'], reverse=True)

# Assign ranks
for i, m in enumerate(scored):
    m['rank'] = i + 1

# Print table
print(f"{'Rank':<4} {'Model':<35} {'Provider':<20} {'Score':<6} {'Time':<6} {'Tasks':<5} {'Quality':<10} {'Ctx':<8} {'Status':<10}")
print("-" * 120)
for m in scored:
    ctx_str = f"{m['ctx']//1000}K" if m['ctx'] > 0 else "N/A"
    print(f"{m['rank']:<4} {m['model'][:35]:<35} {m['provider'][:20]:<20} {m['score']:<6.1f} {m['time']:<6.1f} {m['tasks_done']}/5    {m['quality']:<10} {ctx_str:<8} {m['status']:<10}")

# Save full results
with open(r'C:\Users\eg_di\.config\opencode\final_test_results.json', 'w') as f:
    json.dump(scored, f, indent=2)

print(f"\nTotal models scored: {len(scored)}")
print("Saved to final_test_results.json")