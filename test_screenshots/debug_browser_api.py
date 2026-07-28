import asyncio, json, uuid
import httpx

async def main():
    sid = uuid.uuid4().hex[:12]
    client = httpx.AsyncClient(timeout=httpx.Timeout(60))
    async with client.stream(
        "POST",
        "http://localhost:8000/v1/task/execute",
        json={"session_id": sid, "description": "Navigate to https://www.google.com and tell me the title"},
    ) as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data:"):
                try:
                    ev = json.loads(line[5:].strip())
                    t = ev.get("type")
                    if t in ("tool_call", "tool_result"):
                        tool = ev.get("payload", {}).get("tool", "")
                        s = ev.get("payload", {}).get("success", None)
                        print(f"{t}: tool={tool}, success={s}")
                        if t == "tool_result" and tool == "browser":
                            p = ev.get("payload", {})
                            print(f"  stdout: {p.get('stdout', '')[:100]}")
                            meta = p.get("metadata", {})
                            print(f"  metadata keys: {list(meta.keys())}")
                    elif t in ("task_completed", "task_failed"):
                        print(f"{t}")
                except json.JSONDecodeError:
                    pass
    await client.aclose()

asyncio.run(main())
