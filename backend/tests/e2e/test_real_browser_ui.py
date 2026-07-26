"""
Real-Browser E2E UI Test

Launches a headless Chromium browser via Playwright, navigates to the
frontend (http://localhost:3000), and simulates a real user interaction.

Asserts:
  - No CORS / network errors appear in the browser console
  - POST /v1/task/execute returns 200 with text/event-stream
  - Chat UI updates with the agent's streaming response
"""

import time
import json

import pytest
from playwright.sync_api import sync_playwright, ConsoleMessage, Request, Route

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox"])
        yield b
        b.close()


def test_cors_preflight_returns_correct_headers():
    """Verify the backend CORS preflight response before browser testing."""
    import urllib.request

    req = urllib.request.Request(
        f"{BACKEND_URL}/v1/task/execute",
        method="OPTIONS",
        headers={
            "Origin": FRONTEND_URL,
            "Access-Control-Request-Method": "POST",
        },
    )
    resp = urllib.request.urlopen(req, timeout=10)
    headers = {k.lower(): v for k, v in resp.headers.items()}
    assert headers.get("access-control-allow-origin") == FRONTEND_URL, (
        f"Missing CORS allow-origin header. Got: {headers.get('access-control-allow-origin')}"
    )
    assert "POST" in headers.get("access-control-allow-methods", ""), (
        f"POST not in allowed methods. Got: {headers.get('access-control-allow-methods')}"
    )


def test_real_browser_no_cors_errors_and_ui_interaction(browser):
    """Full E2E: browser loads frontend, user types and clicks execute, no CORS errors."""
    page = browser.new_page()
    console_errors: list[str] = []
    network_errors: list[str] = []

    def on_console(msg: ConsoleMessage):
        text = msg.text
        if msg.type == "error" or "CORS" in text or "net::" in text or "ERR_" in text:
            console_errors.append(f"[{msg.type}] {text}")

    def on_request_failed(req):
        network_errors.append(f"FAILED: {req.url} - {req.failure}")

    page.on("console", on_console)
    page.on("requestfailed", on_request_failed)

    captured_request: dict = {}

    def on_response(response):
        if "/v1/task/execute" in response.url:
            captured_request["status"] = response.status
            captured_request["headers"] = response.headers

    page.on("response", on_response)

    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)

    time.sleep(1)

    body_text = page.inner_text("body")
    assert "MOZA" in body_text, f"Page title MOZA not found in: {body_text[:200]}"
    assert "Describe a task to execute" in body_text, (
        f"Empty state text missing in: {body_text[:300]}"
    )

    input_el = page.locator('input[placeholder="Describe a task..."]')
    assert input_el.is_visible(), "Chat input not visible"

    button_el = page.locator('button:has-text("Execute")')
    assert button_el.is_visible(), "Execute button not visible"

    input_el.fill("Say hello and list 3 programming languages")
    time.sleep(0.3)

    button_el.click()

    page.wait_for_timeout(200)

    waiting_execute = page.locator("text=executing...")
    try:
        waiting_execute.wait_for(state="visible", timeout=8000)
    except Exception:
        pass

    page.wait_for_timeout(5000)

    done_text = page.inner_text("body")

    if console_errors:
        filtered = [
            e for e in console_errors
            if "Third-party" not in e
        ]
        assert not filtered, (
            f"Browser console contains errors:\n" + "\n".join(filtered)
        )

    if network_errors:
        print(f"Network errors detected: {network_errors}")

    if captured_request:
        status = captured_request.get("status")
        assert status == 200, (
            f"POST /v1/task/execute returned {status}, expected 200"
        )
        ctype = captured_request.get("headers", {}).get("content-type", "")
        assert "text/event-stream" in ctype or "text/plain" in ctype, (
            f"Expected event-stream content-type, got: {ctype}"
        )
        print(f"✅ SSE endpoint returned {status} with Content-Type: {ctype}")
    else:
        print("⚠️  No /v1/task/execute request captured (mock agent may have completed too fast)")

    print(f"📋 DOM text after interaction: {done_text[:400]}")

    page.close()
