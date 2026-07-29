content = "I'm sorry, but I currently don't have the ability to create files directly. However, I can guide you through the process! Would you like some help with that?"
lowered = content.lower()
tool_keywords = {"filesystem": ["write file", "create file", "save file", "write to"]}
for tool_name, triggers in tool_keywords.items():
    for trigger in triggers:
        result = trigger in lowered
        print(f"{repr(trigger)} in lowered: {result}")
# Also test the re.search for path
import re
pm = re.search(r'(?:to|in|at|:)\s*([A-Za-z]:\\[^\s"\']+)', content)
print(f"Path match: {pm}")
if pm:
    print(f"Path: {pm.group(1)}")
