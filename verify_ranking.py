import json

with open('C:/Users/eg_di/.config/opencode/opencode.jsonc') as f:
    config = json.load(f)

print('=' * 80)
print('FINAL OPENCODE MODEL SELECTION LIST (Ranked by Priority)')
print('=' * 80)
rank = 0
for provider_name, provider_data in config['provider'].items():
    for model_id, model_data in provider_data['models'].items():
        rank += 1
        name = model_data['name']
        print(f'  {rank:2d}. {name}')
print('=' * 80)
print(f'Total models: {rank}')
print(f'Total providers: {len(config["provider"])}')
print('Providers in order:', list(config['provider'].keys()))