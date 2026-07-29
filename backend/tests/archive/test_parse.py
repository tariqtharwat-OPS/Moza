import json, ast

# The format the model might return (Python dict literal with single quotes)
s1 = """{'name': 'filesystem', 'arguments': {'action': 'write', 'path': 'D:\\Moza\\hello.txt', 'content': 'Hello World'}}"""

print("Original:", s1)

# Try ast.literal_eval first (handles Python dict literals)
try:
    d = ast.literal_eval(s1)
    print("ast.literal_eval works:", d)
except Exception as e:
    print("ast.literal_eval error:", e)

# Try replacing single quotes with double quotes for JSON parsing
s2 = s1.replace("'", '"')
try:
    d2 = json.loads(s2)
    print("json.loads after quote replace works:", d2)
except json.JSONDecodeError as e:
    print("json.loads after quote replace error:", e)
