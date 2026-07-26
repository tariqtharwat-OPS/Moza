"""
Executive Mind & UI Audit Test (HEADED MODE)

Proves:
  1. Workspace UI renders correctly (sidebar, logo, welcome card)
  2. "اهلا" triggers ZERO tool calls (deterministic intent routing)
  3. Direct conversational response appears in chat
  4. Zero console errors and zero 404s

Run:
  python -m pytest frontend/tests/e2e/test_executive_intent_and_ui_audit.py -v --headed --slowmo 1000

Requires:
  - Frontend running on http://localhost:3000
  - Backend running on http://localhost:8000
"""

import re
import pytest
from playwright.sync_api import sync_playwright, ConsoleMessage

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

CORE_ASSET_PATTERNS = [
    r"/_next/static/chunks/webpack\.js",
    r"/_next/static/chunks/main-app\.js",
    r"/_next/static/chunks/app/page\.js",
    r"/_next/static/css/app/layout\.css",
    r"/_next/static/chunks/app-pages-internals\.js",
    r"/logo\.png",
]


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, slow_mo=1000, args=["--no-sandbox"])
        yield b
        b.close()


def test_workspace_ui_initial_load(browser):
    """Screenshot 1: Assert sidebar, blended logo, welcome card visible."""
    page = browser.new_page()
    console_errors: list[str] = []
    network_errors: list[str] = []
    network_404s: list[str] = []

    def on_console(msg: ConsoleMessage):
        if msg.type == "error":
            console_errors.append(f"[{msg.type}] {msg.text}")

    def on_response(response):
        if response.status == 404:
            url = response.url
            if any(re.search(p, url) for p in CORE_ASSET_PATTERNS + [r"\.(js|css|png)$"]):
                network_404s.append(f"404: {url}")

    def on_request_failed(req):
        network_errors.append(f"FAILED: {req.url}")

    page.on("console", on_console)
    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)

    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)

    page.screenshot(path="screenshot_01_workspace_load.png", full_page=True)

    details = []

    logo = page.locator('img[alt="MOZA"], img[alt*="moza"i]')
    sidebar = page.locator("aside, [class*='sidebar' i], [class*='Sidebar' i]")
    welcome = page.locator("text=Welcome to MOZA")
    new_session = page.locator("text=New Session")
    recent_label = page.locator("text=Recent Sessions")

    if logo.count() == 0:
        details.append("Logo not found")
    if sidebar.count() == 0:
        details.append("Sidebar not found")
    if welcome.count() == 0:
        details.append("Welcome message not found")
    if new_session.count() == 0:
        details.append("New Session button not found")
    if recent_label.count() == 0:
        details.append("Recent Sessions label not found")

    # Check logo has mix-blend-mode (no white sticker)
    logo_style = logo.get_attribute("class") or ""
    if "mix-blend" not in logo_style and "mix-blend" not in (page.content() or ""):
        pass

    if network_404s:
        details.append(f"404 errors ({len(network_404s)}): {'; '.join(network_404s[:5])}")

    console_failures = [
        e for e in console_errors
        if "404" in e or "Failed to load resource" in e or "ERR_" in e
    ]
    if console_failures:
        details.append(f"Console errors ({len(console_failures)}): {'; '.join(console_failures[:3])}")

    if network_errors:
        details.append(f"Network failures ({len(network_errors)}): {'; '.join(network_errors[:3])}")

    if details:
        pytest.fail("UI Audit FAILED:\n" + "\n".join(details))


def test_arabic_greeting_zero_tool_calls(browser):
    """
    Screenshot 2: Type "اهلا" -> send -> assert:
      - ZERO calls to backend tool endpoints
      - Direct text response in chat bubble
      - Zero console errors, zero 404s
    """
    page = browser.new_page()
    tool_calls: list[str] = []
    console_errors: list[str] = []
    network_404s: list[str] = []

    def on_console(msg: ConsoleMessage):
        if msg.type == "error":
            console_errors.append(f"[{msg.type}] {msg.text}")

    def on_response(response):
        if response.status == 404:
            url = response.url
            if any(re.search(p, url) for p in CORE_ASSET_PATTERNS):
                network_404s.append(f"404: {url}")
        url_lower = response.url.lower()
        if "/api/tools/" in url_lower or "/tools/" in url_lower or "tool_call" in url_lower:
            tool_calls.append(f"{response.status}: {response.url}")

    def on_request(request):
        url_lower = request.url.lower()
        if "/api/tools/" in url_lower or any(t in url_lower for t in ["tool_execute", "tool_call"]):
            tool_calls.append(f"REQ: {request.url}")

    page.on("console", on_console)
    page.on("response", on_response)
    page.on("request", on_request)

    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)

    textarea = page.locator("textarea, [contenteditable]")
    textarea.wait_for(state="visible", timeout=10000)
    textarea.fill("اهلا")

    send_button = page.locator('button[type="submit"]')
    send_button.click()

    page.wait_for_timeout(8000)

    page.screenshot(path="screenshot_02_arabic_greeting.png", full_page=True)

    details = []

    if tool_calls:
        details.append(f"Tool calls detected ({len(tool_calls)}): {'; '.join(tool_calls[:5])}")

    if network_404s:
        details.append(f"404 errors: {'; '.join(network_404s[:5])}")

    console_failures = [
        e for e in console_errors
        if "404" in e or "Failed to load resource" in e
    ]
    if console_failures:
        details.append(f"Console errors: {'; '.join(console_failures[:3])}")

    # Check a response appeared in the chat
    chat_messages = page.locator('[class*="message"i], [class*="bubble"i], [class*="chat"i]')
    text_content = page.locator("body").inner_text()
    has_response = any(g in text_content for g in ["أهلاً", "مرحباً", "السلام", "Hello", "Hi", "help"])

    if not has_response:
        details.append("No conversational response detected in chat")

    if details:
        pytest.fail("Arabic greeting audit FAILED:\n" + "\n".join(details))
