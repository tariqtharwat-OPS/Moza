import json

# Load all test results
with open(r'C:\Users\eg_di\.config\opencode\retest_results.json') as f:
    retest = json.load(f)
with open(r'C:\Users\eg_di\.config\opencode\github_models_stress.json') as f:
    github = json.load(f)

# Build complete model list
results = retest + github

# Model context windows
CTX = {
    'llama-3.3-70b-versatile': 128000,
    'llama-3.1-8b-instant': 8000,
    'qwen/qwen3.6-27b': 32000,
    'codestral-latest': 256000,
    'mistral-small-latest': 32000,
    'mistral-large-latest': 128000,
    'ministral-8b-latest': 32000,
    'Meta-Llama-3.1-405B-Instruct': 128000,
    'Meta-Llama-3.1-8B-Instruct': 8000,
    'gpt-4o': 128000,
    'gpt-4o-mini': 128000,
}

# Also include models from stress_results.json that weren't retested
with open(r'C:\Users\eg_di\.config\opencode\stress_results.json') as f:
    stress = json.load(f)

# Map stress results to our expected keys
stress_map = {}
for r in stress:
    key = f"{r['Model']}|{r['Provider']}"
    stress_map[key] = {
        'model': r['Model'],
        'provider': r['Provider'],
        'status_code': 200 if r['Status'] == 'success' else 0,
        'time': r['Time'],
        'tasks_done': r['TasksDone'],
        'quality': r['Quality'],
        'context_ok': r['ContextOk'] == 'yes',
        'error': r['Error'],
    }

# Map retest results
for r in retest:
    key = f"{r['model']}|{r['model_id']}"
    stress_map[key] = {
        'model': r['model'],
        'provider': r['provider'],
        'status_code': r.get('status_code', 200),
        'time': r.get('time', 0),
        'tasks_done': r.get('tasks_done', 0),
        'quality': r.get('quality', 'invalid'),
        'context_ok': r.get('tasks_done', 0) > 0,
        'error': r.get('error', ''),
    }

# Map github results
for r in github:
    key = f"{r['model']}|{r['provider']}"
    stress_map[key] = {
        'model': r['model'],
        'provider': r['provider'],
        'status_code': 200 if r['status'] == 'success' else 0,
        'time': r['time'],
        'tasks_done': r['tasks_done'],
        'quality': r['quality'],
        'context_ok': r.get('context_ok', r['tasks_done'] > 0),
        'error': r.get('error', ''),
    }

# Score each model
QUAL = {'excellent': 100, 'good': 75, 'poor': 50, 'partial': 25, 'invalid': 0}

scored = []
for key, m in stress_map.items():
    model = m['model']
    provider = m['provider']
    ctx = CTX.get(model, 0)
    status_code = m['status_code']
    time = m['time']
    tasks = m['tasks_done']
    quality = m['quality']
    ctx_ok = m['context_ok']
    
    s = 100 if status_code == 200 else 0
    sp = max(0, (120 - time) / 120 * 100)
    q = QUAL.get(quality, 0)
    c = 100 if ctx_ok and ctx >= 4000 else (50 if ctx_ok else 0)
    
    total = s * 0.40 + sp * 0.25 + q * 0.25 + c * 0.10
    
    scored.append({
        'model': model,
        'provider': provider,
        'time': time,
        'tasks_done': tasks,
        'quality': quality,
        'ctx': ctx,
        'context_ok': ctx_ok,
        'status': 'success' if status_code == 200 else 'failed',
        'score': total,
        'error': m.get('error', '')
    })

# Sort by score descending
scored.sort(key=lambda x: x['score'], reverse=True)
for i, m in enumerate(scored):
    m['rank'] = i + 1

# Print top 25
print(f"{'Rank':<4} {'Model':<35} {'Provider':<20} {'Score':<6} {'Time':<7} {'Tasks':<5} {'Quality':<10} {'Ctx':<8}")
print("-" * 100)
for m in scored[:25]:
    ctx_s = f"{m['ctx']//1000}K" if m['ctx'] > 0 else "N/A"
    t = f"{m['time']:.2f}" if m['time'] else "N/A"
    print(f"{m['rank']:<4} {m['model'][:35]:<35} {m['provider'][:20]:<20} {m['score']:<6.1f} {t:<7} {m['tasks_done']}/5    {m['quality']:<10} {ctx_s:<8}")

print(f"\nTotal: {len(scored)} models scored")

# Save
with open(r'C:\Users\eg_di\.config\opencode\final_test_results.json', 'w') as f:
    json.dump(scored, f, indent=2)

# Filter to working success models only for config
working = [m for m in scored if m['status'] == 'success']
print(f"\nWorking (success) models: {len(working)}")
for m in working:
    print(f"  {m['rank']}. {m['model'][:35]:35s} {m['provider']:20s} {m['score']:.1f}")
