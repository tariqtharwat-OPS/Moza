import json, hashlib

print("=" * 60)
print("CONFIG SYNC VERIFICATION")
print("=" * 60)

# 1. Verify opencode configs match
with open(r'D:\Moza\opencode.json') as f:
    opencode = json.load(f)
with open(r'C:\Users\eg_di\.config\opencode\opencode.jsonc') as f:
    opencode_jsonc = json.load(f)

c1 = json.dumps(opencode, sort_keys=True)
c2 = json.dumps(opencode_jsonc, sort_keys=True)
print(f"\nD:\\Moza\\opencode.json == C:\\...\\opencode.jsonc: {c1 == c2}")

# 2. Verify orchestrator config
with open(r'D:\Moza\packages\moza-orchestrator\config.json') as f:
    orch = json.load(f)

# 3. Check all model names match between opencode and orchestrator
oc_models = {}
for prov, conf in opencode['provider'].items():
    for model, mconf in conf['models'].items():
        oc_models[f"{prov}/{model}"] = True

print("\n--- Models in orchestrator ranking ---")
all_match = True
for entry in orch['ranking']:
    key = f"{entry['provider']}/{entry['model']}"
    found = key in oc_models
    if not found:
        print(f"  MISSING: {key} (rank {entry['rank']})")
        all_match = False
    else:
        print(f"  OK: {key} (rank {entry['rank']})")

print(f"\nAll orchestrator models found in opencode config: {all_match}")

# 4. Check API keys match
print("\n--- API Key consistency ---")
all_keys_match = True
for prov, conf in opencode['provider'].items():
    oc_key = conf['options']['apiKey']
    if prov in orch['apiKeys']:
        or_key = orch['apiKeys'][prov]
        match = oc_key == or_key
        if not match:
            print(f"  MISMATCH: {prov}")
            all_keys_match = False
        else:
            print(f"  OK: {prov}")

print(f"\nAll API keys match: {all_keys_match}")

# 5. File sizes
import os
files = [
    r'D:\Moza\opencode.json',
    r'C:\Users\eg_di\.config\opencode\opencode.jsonc',
    r'D:\Moza\constitution.yaml',
    r'D:\Moza\packages\moza-orchestrator\config.json',
    r'C:\Users\eg_di\.config\opencode\ranked_models.json',
    r'D:\Moza\packages\moza-orchestrator\pyproject.toml',
]
print("\n--- File sizes ---")
for f in files:
    if os.path.exists(f):
        print(f"  {os.path.basename(f):40s} {os.path.getsize(f):>6} bytes")
    else:
        print(f"  {os.path.basename(f):40s} NOT FOUND")
