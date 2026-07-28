import asyncio, json, uuid
import httpx

async def main():
    sid = uuid.uuid4().hex[:12]
    client = httpx.AsyncClient(timeout=httpx.Timeout(60))
    async with client.stream(
        "POST",
        "http://localhost:8000/v1/task/execute",
        json={"session_id": sid, "description": "Navigate to https://www.google.com"},
    ) as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data:"):
                try:
                    ev = json.loads(line[5:].strip())
                    if ev.get("type") == "tool_result" and ev.get("payload", {}).get("tool") == "browser":
                        p = ev.get("payload", {})
                        print("TOOL RESULT PAYLOAD KEYS:", list(p.keys()))
                        for k in ["metadata", "screenshot_base64", "screenshot_path", "success", "stdout", "title", "url", "duration_ms"]:
                            v = p.get(k)
                            if v is not None:
                                if k == "metadata":
                                    print(f"  metadata keys: {list(v.keys())}")
                                    sb64 = v.get("screenshot_base64", "")
                                    print(f"  metadata.screenshot_base64 len: {len(sb64)}")
                                else:
                                    s = str(v)
                                    print(f"  {k}: {s[:120]}..." if len(s) > 120 else f"  {k}: {s}")
                except json.JSONDecodeError:
                    pass
    await client.aclose()
    print("\nDONE")

asyncio.run(main())
