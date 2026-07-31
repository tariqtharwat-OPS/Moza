from moza.core.response_normalizer import normalize_streaming_chunk

# Test with a simple dictionary
chunk = {'choices': [{'delta': {'content': 30}}]}

print(f'Before: {type(chunk["choices"][0]["delta"]["content"])}')
print(f'Value: {chunk["choices"][0]["delta"]["content"]}')

normalized = normalize_streaming_chunk(chunk)

print(f'\nAfter: {type(normalized["choices"][0]["delta"]["content"])}')
print(f'Value: {normalized["choices"][0]["delta"]["content"]}')

if isinstance(normalized["choices"][0]["delta"]["content"], str):
    print('\n✓ Test PASSED: Content is now a string')
else:
    print(f'\n✗ Test FAILED: Content is still {type(normalized["choices"][0]["delta"]["content"])}')
