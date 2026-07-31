"""Simple test: verify tool calling works end-to-end."""
import httpx
import json
import time

DESCRIPTION = "Create a file named hello.txt in D:\\Moza with content 'Hello World'"

print("=== SIMPLE TEST: Tool Calling Verification ===")
print(f"Task: {DESCRIPTION}")
print()

start = time.time()
tool_calls_seen = []

with httpx.Client(timeout=300.0) as client:
    with client.stream(
        "POST",
        "http://localhost:8000/v1/task/execute",
        json={"description": DESCRIPTION, "workspace_path": ""},
    ) as resp:
        print(f"HTTP {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            exit(1)
        buffer = ""
        is_data = False
        for chunk in resp.iter_bytes():
            buffer += chunk.decode(errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line.startswith("event: step"):
                    is_data = True
                elif is_data and line.startswith("data: "):
                    is_data = False
                    ev = json.loads(line[6:])
                    etype = ev["type"]
                    elapsed = time.time() - start

                    if etype == "tool_call":
                        tool_calls_seen.append(ev)
                        print(f"\n*** TOOL_CALL [{elapsed:.1f}s] ***")
                        print(f"  Tool: {ev['payload']['tool']}")
                        print(f"  Args: {json.dumps(ev['payload']['args'], indent=2, ensure_ascii=False)}")
                        print(f"  RAW PAYLOAD: {json.dumps(ev, indent=2, ensure_ascii=False)}")
                    elif etype == "tool_result":
                        result = ev["payload"]
                        success = result.get("success", "?")
                        stdout = str(result.get("stdout", ""))[:300]
                        stderr = str(result.get("stderr", ""))[:300]
                        print(f"  TOOL_RESULT [{elapsed:.1f}s]: {result.get('tool','?')} success={success}")
                        if stdout:
                            print(f"    stdout: {stdout}")
                        if stderr:
                            print(f"    stderr: {stderr}")
                    elif etype == "llm_token":
                        content = ev["payload"].get("content", "")
                        if content.strip():
                            print(f"  LLM_TOKEN ({len(content)} chars):\n{content}\n---")
                    elif etype == "llm_finished":
                        print(f"  LLM_FINISHED [{elapsed:.1f}s]")
                    elif etype == "task_completed":
                        print(f"  TASK_COMPLETED [{elapsed:.1f}s]")
                    elif etype == "task_failed":
                        print(f"  TASK_FAILED [{elapsed:.1f}s]: {ev['payload']}")
                    elif etype == "agent_thinking":
                        pass  # skip noise
                    else:
                        print(f"  {etype} [{elapsed:.1f}s]")

total_time = time.time() - start
print(f"\n=== RESULTS ===")
print(f"Total runtime: {total_time:.1f}s")
print(f"Tool calls executed: {len(tool_calls_seen)}")

import os
path = "D:\\Moza\\hello.txt"
exists = os.path.exists(path)
size = os.path.getsize(path) if exists else 0
print(f"\nFile D:\\Moza\\hello.txt: exists={exists}, size={size} bytes")
if exists:
    content = open(path, "r").read()
    print(f"Content: {content}")
