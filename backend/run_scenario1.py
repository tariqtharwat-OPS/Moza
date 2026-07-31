"""Scenario 1: Multi-Step Execution (Success Path)"""
import httpx
import json
import time

DESCRIPTION = (
    '\u0627\u0628\u062d\u062b \u0639\u0646 \u0623\u0641\u0636\u0644 10 '
    '\u0645\u0633\u062a\u0648\u0631\u062f\u064a\u0646 \u0644\u0633\u0645\u0643 '
    'Red Snapper \u0641\u064a \u0645\u0627\u0644\u064a\u0632\u064a\u0627\u060c '
    '\u062b\u0645 \u0623\u0646\u0634\u0626 \u0627\u0644\u062a\u0642\u0627\u0631\u064a\u0631 '
    '\u0627\u0644\u062a\u0627\u0644\u064a\u0629 \u0641\u064a \u0645\u062c\u0644\u062f '
    'D:\\Moza: buyers.html, buyers.xlsx, buyers.pdf'
)

print("=== SCENARIO 1: Multi-Step Execution (Success Path) ===")
print(f"Task: {DESCRIPTION}")
print()

start = time.time()
tool_calls_seen = []
events_by_type = {}

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
                    events_by_type.setdefault(etype, []).append(ev)

                    if etype == "tool_call":
                        tool_calls_seen.append(ev)
                        tname = ev["payload"]["tool"]
                        args_str = json.dumps(
                            ev["payload"]["args"], ensure_ascii=False
                        )[:300]
                        print(
                            f"  [{elapsed:.1f}s] TOOL_CALL: {tname} "
                            f"args={args_str}"
                        )
                    elif etype == "tool_result":
                        result = ev["payload"]
                        success = result.get("success", "?")
                        stdout = str(result.get("stdout", ""))[:200]
                        print(
                            f"  [{elapsed:.1f}s] TOOL_RESULT: "
                            f"{result.get('tool','?')} "
                            f"success={success} stdout={stdout}"
                        )
                    elif etype == "llm_token":
                        content = ev["payload"].get("content", "")[:100]
                        print(f"  [{elapsed:.1f}s] LLM_TOKEN: {content}")
                    elif etype == "llm_finished":
                        print(f"  [{elapsed:.1f}s] LLM_FINISHED")
                    elif etype == "task_completed":
                        print(f"  [{elapsed:.1f}s] TASK_COMPLETED")
                    elif etype == "task_failed":
                        print(
                            f"  [{elapsed:.1f}s] TASK_FAILED: {ev['payload']}"
                        )
                    elif etype == "browser_started":
                        print(f"  [{elapsed:.1f}s] BROWSER_STARTED")
                    elif etype == "browser_action":
                        action = ev["payload"].get("action", "?")
                        print(f"  [{elapsed:.1f}s] BROWSER_ACTION: {action}")
                    else:
                        print(f"  [{elapsed:.1f}s] {etype}")

total_time = time.time() - start
print()
print("=== RESULTS ===")
print(f"Total runtime: {total_time:.1f}s")
print(f"Tool calls executed: {len(tool_calls_seen)}")
for tc in tool_calls_seen:
    print(
        f"  - {tc['payload']['tool']}: "
        f"{json.dumps(tc['payload']['args'], ensure_ascii=False)[:500]}"
    )
print(
    f"Events by type: {[(k, len(v)) for k, v in sorted(events_by_type.items())]}"
)

# File verification
print()
print("=== FILE VERIFICATION ===")
import os
for pattern in ["buyers.html", "buyers.xlsx", "buyers.pdf"]:
    path = os.path.join("D:\\Moza", pattern)
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"  D:\\Moza\\{pattern}: exists={exists}, size={size} bytes")
