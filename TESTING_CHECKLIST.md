# Manual Testing Checklist — Phase 3.3 Frontend E2E Integration

> Run these tests locally after starting backend + frontend.
> All tests assume the Regression Freeze (Phase 3.2.5) is intact.

## Prerequisites

```bash
# Terminal 1: Start Backend
cd backend
pip install -r requirements.txt
python -m uvicorn moza.api.main:app --reload --port 8000

# Terminal 2: Start Frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in a browser.

---

## Test 1: Chat & SSE Streaming

**Steps:**
1. Type `"Say hello and list 3 programming languages"` in the input box.
2. Click **Execute**.

**Expected:**
- [ ] Thinking dots (3 bouncing dots) appear immediately.
- [ ] LLM tokens stream in one word at a time with a blinking cursor.
- [ ] The full response appears in a chat bubble.
- [ ] "executing..." label shows in the header while streaming.
- [ ] "executing..." disappears and input re-enables when done.
- [ ] No broken JSON or UI crashes. ❌

---

## Test 2: Terminal Visualization

**Steps:**
1. Type `"List files in the current directory"` and click Execute.

**Expected:**
- [ ] A terminal pane (dark background, 240px height) appears below the chat.
- [ ] The command `$ ls` (or `$ dir` on Windows) appears in green text inside the terminal.
- [ ] The command output (file names) appears in the terminal pane below the command.
- [ ] Terminal uses xterm.js with JetBrains Mono font.
- [ ] Multiple terminal commands stack in the same terminal view.

---

## Test 3: Browser Visualization

**Steps:**
1. Type `"Navigate to https://www.python.org and tell me the page title"` and click Execute.

**Expected:**
- [ ] A "Browser" panel appears with a URL bar and screenshot area.
- [ ] URL updates to `https://www.python.org/` (or similar).
- [ ] A screenshot of the Python.org homepage appears (may take 10-30s).
- [ ] The "View" / "Actions" tabs work (click to switch).
- [ ] Actions tab lists the browser actions taken (navigate, extract_text, screenshot).
- [ ] Screenshot data renders correctly (not broken image).

---

## Test 4: Approval UI Flow

**Steps:**
1. Type a potentially destructive command like `"Delete the test file"` and click Execute.

**Expected:**
- [ ] An "Approval Required" banner appears with amber/yellow styling.
- [ ] The banner shows the tool name and description.
- [ ] Two buttons are visible: "Approve" (green) and "Reject" (red).
- [ ] Clicking **Approve** changes button to "Approving..." then the task continues.
- [ ] Clicking **Reject** changes button to "Rejecting..." then the task stops.
- [ ] Banner disappears after action is taken.
- [ ] No UI crashes after clicking either button. ❌

**Alternative Test (if backend doesn't trigger approval):**
1. Check the backend's `orchestrator.py` to ensure `requires_confirmation: True` is set on tools.
2. The `browser` tool has `requires_confirmation: True` by default.
3. Type `"Open a browser window"` — this should trigger WAITING_APPROVAL.

---

## Test 5: Full Integrated E2E Flow

**Steps:**
1. Type `"Research Python 3.8.0 vs 3.9.0 on the local server at http://localhost:8000"` (Note: this won't work since the fixture server isn't running; use a simpler task instead).
2. Instead, type `"Write a Python script that prints the Fibonacci sequence to a file named fib.py, then run it with python"` and click Execute.

**Expected:**
- [ ] Chat shows: tool_call (filesystem write), tool_result (success), tool_call (terminal execute), tool_result (stdout).
- [ ] Terminal pane shows: `$ python fib.py` and the Fibonacci output.
- [ ] Final message confirms the task completed.
- [ ] Multiple event types render simultaneously (chat + terminal).
- [ ] All 81 backend tests still pass after test completes.

---

## Test 6: Error Handling

**Steps:**
1. Stop the backend (`Ctrl+C` in Terminal 1).
2. Type `"Say hello"` and click Execute.

**Expected:**
- [ ] A "Task failed: Connection failed" message appears (red ✕).
- [ ] The input re-enables.
- [ ] No blank screen or frozen UI. ❌
- [ ] Starting the backend again and submitting a new task works.

---

## Pass Criteria

- [ ] All 6 tests pass without UI crashes, broken JSON, or frozen states.
- [ ] SSE streaming renders tokens in real-time.
- [ ] Terminal component shows xterm output for terminal tool calls.
- [ ] Browser component shows screenshots for browser tool calls.
- [ ] Approval banner shows and responds to approve/reject clicks.
- [ ] Error states handled gracefully (no blank screen).
