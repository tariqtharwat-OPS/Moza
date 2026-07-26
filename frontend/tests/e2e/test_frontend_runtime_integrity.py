"""
Frontend Runtime Integrity Test

Verifies the Next.js frontend serves all assets correctly:
  a. Navigates to http://localhost:3000
  b. Intercepts all console messages and network requests
  c. FAILS if any 404 status codes detected for core JS/CSS assets
  d. FAILS if "Failed to load resource" errors appear in the console
  e. Asserts main chat container or logo is visible on the page
"""

import re
import pytest
from playwright.sync_api import sync_playwright, ConsoleMessage, Request, Route

FRONTEND_URL = "http://localhost:3000"

# Assets that must never 404
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
        b = p.chromium.launch(headless=True, args=["--no-sandbox"])
        yield b
        b.close()


def test_frontend_loads_with_zero_404s(browser):
    page = browser.new_page()
    console_errors: list[str] = []
    network_404s: list[str] = []

    def on_console(msg: ConsoleMessage):
        text = msg.text
        if msg.type == "error":
            console_errors.append(f"[{msg.type}] {text}")

    def on_response(response):
        if response.status == 404:
            url = response.url
            if any(re.search(p, url) for p in CORE_ASSET_PATTERNS):
                network_404s.append(f"404: {url}")

    page.on("console", on_console)
    page.on("response", on_response)

    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)

    page.wait_for_timeout(3000)

    details = []

    if network_404s:
        details.append(f"Core asset 404s ({len(network_404s)}):")
        for e in network_404s:
            details.append(f"  {e}")

    console_failures = [
        e for e in console_errors
        if "404" in e or "Failed to load resource" in e
    ]
    if console_failures:
        details.append(f"Console errors ({len(console_failures)}):")
        for e in console_failures:
            details.append(f"  {e}")

    if details:
        pytest.fail("Frontend integrity check FAILED:\n" + "\n".join(details))


def test_logo_or_chat_visible(browser):
    page = browser.new_page()
    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)

    logo = page.locator('img[alt*="logo"i], img[alt*="Logo"i], img[src*="logo"]')
    chat = page.locator('[class*="chat"i], [class*="Chat"i], textarea, [contenteditable]')

    logo_visible = logo.is_visible() if logo.count() > 0 else False
    chat_visible = chat.is_visible() if chat.count() > 0 else False

    assert logo_visible or chat_visible, (
        f"Neither logo (count={logo.count()}) nor chat input (count={chat.count()}) is visible"
    )
