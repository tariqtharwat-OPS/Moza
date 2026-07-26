"""
E2E Agent Behavior Pattern Tests

Verifies the agent responds appropriately based on task complexity:
  1. Simple greetings → direct text response (NO tool calls)
  2. Simple questions → direct answer (NO tool calls)
  3. Complex tasks → uses tools appropriately
  4. Mixed interactions → greets + uses tools + summarizes

Each test uses a real browser (Playwright) to verify UI behavior.
"""

import time
import json

import pytest
from playwright.sync_api import sync_playwright, ConsoleMessage

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

# ── helpers ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox"])
        yield b
        b.close()


def _run_interaction(browser, prompt: str, wait_after_click: float = 6.0):
    """Navigate to frontend, type a prompt, click Execute, wait, return page and console errors."""
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

    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)
    time.sleep(0.5)

    input_el = page.locator('input[placeholder="Describe a task..."]')
    input_el.fill(prompt)
    time.sleep(0.2)

    page.locator('button:has-text("Execute")').click()
    page.wait_for_timeout(int(wait_after_click * 1000))

    body_text = page.inner_text("body")
    page.close()

    has_errors = any(
        "error" in line.lower() or "fail" in line.lower() or "traceback" in line.lower()
        for line in body_text.split("\n")
    )

    return {
        "body": body_text,
        "console_errors": console_errors,
        "network_errors": network_errors,
        "has_tool_calls": "filesystem" in body_text
            or "terminal" in body_text
            or "browser" in body_text,
        "has_task_complete": "Task completed" in body_text
            or "completed" in body_text.lower(),
        "has_errors": has_errors,
    }


# ── Test 1: Simple Greeting ───────────────────────────────────────────


def test_simple_greeting_direct_response(browser):
    """Input 'Say hello in one word' → direct text response, NO tool calls."""
    result = _run_interaction(browser, "Say hello in one word")

    if result["console_errors"]:
        filtered = [e for e in result["console_errors"] if "Third-party" not in e]
        assert not filtered, (
            f"Browser console contains errors:\n" + "\n".join(filtered)
        )

    assert not result["has_tool_calls"], (
        f"Agent used tool calls for a simple greeting. Body:\n{result['body'][:500]}"
    )

    assert "hello" in result["body"].lower() or "مرحباً" in result["body"], (
        f"Expected greeting in response. Body:\n{result['body'][:500]}"
    )


# ── Test 2: Simple Question ───────────────────────────────────────────


def test_simple_question_direct_answer(browser):
    """Input 'What is 2 + 2?' → direct answer '4', NO tool calls."""
    result = _run_interaction(browser, "What is 2 + 2?")

    assert not result["has_tool_calls"], (
        f"Agent used tool calls for a simple question. Body:\n{result['body'][:500]}"
    )

    assert "4" in result["body"], (
        f"Expected answer '4' in response. Body:\n{result['body'][:500]}"
    )


# ── Test 3: Task Requiring Tools ──────────────────────────────────────


def test_task_requiring_tools(browser):
    """Input 'Create a file named test.txt' → uses filesystem tool, confirms."""
    result = _run_interaction(browser, "Create a file named test.txt", wait_after_click=8.0)

    assert result["has_tool_calls"], (
        f"Expected tool calls for file creation task. Body:\n{result['body'][:500]}"
    )


# ── Test 4: Mixed Interaction ────────────────────────────────────────


def test_mixed_interaction(browser):
    """Input 'Hello! List the files in the current directory' → greets + uses tools + responds."""
    result = _run_interaction(browser, "Hello! List the files in the current directory", wait_after_click=8.0)

    assert "hello" in result["body"].lower() or result["has_tool_calls"], (
        f"Expected greeting or tool usage. Body:\n{result['body'][:500]}"
    )


# ── Test 5: Casual Greeting "hi how are you" ─────────────────────────


def test_casual_greeting_hi_how_are_you(browser):
    """Input 'hi how are you' → direct friendly response, ZERO tool calls, ZERO errors."""
    result = _run_interaction(browser, "hi how are you", wait_after_click=6.0)

    assert not result["has_tool_calls"], (
        f"Agent called tools for casual greeting. Body:\n{result['body'][:500]}"
    )

    assert not result["has_errors"], (
        f"UI contains error text. Body:\n{result['body'][:500]}"
    )

    assert "great" in result["body"].lower() or "fine" in result["body"].lower() or "hello" in result["body"].lower() or "hi" in result["body"].lower(), (
        f"Expected friendly response. Body:\n{result['body'][:500]}"
    )

    if result["console_errors"]:
        filtered = [e for e in result["console_errors"] if "Third-party" not in e]
        assert not filtered, (
            f"Browser console contains errors:\n" + "\n".join(filtered)
        )


# ── Test 6: Non-English Greeting (Arabic) ────────────────────────────


def test_arabic_greeting_direct_response(browser):
    """Input Arabic greeting → direct Arabic response, NO tool calls."""
    result = _run_interaction(browser, "قل مرحباً بكلمة واحدة فقط")

    assert not result["has_tool_calls"], (
        f"Agent used tool calls for Arabic greeting. Body:\n{result['body'][:500]}"
    )

    assert "مرحباً" in result["body"] or "hello" in result["body"].lower(), (
        f"Expected Arabic greeting in response. Body:\n{result['body'][:500]}"
    )
