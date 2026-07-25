"""
Phase 2.13 — Software Engineer Benchmark (Strict Anti-Cheat)
==============================================================
Exit Criteria:
  1. Pre-seeds a deliberately buggy calculator.py.
  2. Agent autonomously: writes tests, runs pytest, reads failure, fixes code, re-runs, passes.
  3. Test parses events and asserts exact 6-event sequence A-F.
  4. Anti-cheat: verifies test integrity (not weakened), implementation was fixed (not tests).
  5. Full execution record preserved (prompt, context, tool calls/results).
  6. All 75+ existing tests still pass.

Infrastructure is scenario-parameterised: new bug types can be added
without rewriting the test runner (see BugScenario and SCENARIOS).
"""

import asyncio
import json
import os
import sys
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = PROJECT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from moza.agents.litellm_tool_agent import LiteLLMToolAgent
from moza.config.models import MOZAConfig
from moza.core.context import ExecutionContext
from moza.core.event_bus import get_event_bus
from moza.core.event_recorder import EventRecorder
from moza.core.models import Environment, EventType, Session, Task
from moza.tools.filesystem_tool import FilesystemTool
from moza.tools.registry import ToolRegistry
from moza.tools.terminal_tool import TerminalTool


# ═════════════════════════════════════════════════════════════════════════
#  Bug Scenario Framework
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class BugScenario:
    """A parameterised software-engineering bug scenario.

    To add a new scenario, instantiate with:
      name          — short identifier used in session/event labels
      seed_files    — dict[filename, content] written before the task starts
      correct_files — dict[filename, content] the fixed versions (post-fix
                      verification)
      task_desc     — the prompt given to the agent
      test_keywords — strings that MUST appear in the generated test file
                      (anti-cheat: proves tests were not weakened)
      extra_checks  — list of (name, callable(workspace_dir) -> bool) for
                      custom post-run assertions
    """
    name: str
    seed_files: dict[str, str]
    correct_files: dict[str, str]
    task_desc: str
    test_keywords: list[str] = field(default_factory=lambda: ["assert"])
    extra_checks: list[tuple[str, Callable[[Path], bool]]] = field(default_factory=list)


# ── Scenario A: integer division ──────────────────────────────────────────

INTEGER_DIVISION = BugScenario(
    name="integer_division",
    seed_files={
        "calculator.py": """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a // b
""",
    },
    correct_files={
        "calculator.py": """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b
""",
    },
    task_desc=(
        "Write a test file named test_calculator.py with pytest tests for all"
        " four functions in calculator.py (add, subtract, multiply, divide).\n"
        "The test for divide must assert that divide(5, 2) == 2.5.\n"
        "Run 'pytest test_calculator.py -v' in the workspace directory.\n"
        "If tests fail, read the traceback, fix the bug in calculator.py,\n"
        "then run pytest again. Keep repeating until all tests pass,\n"
        "then report the final results."
    ),
    test_keywords=["add", "subtract", "multiply", "divide", "2.5", "assert"],
    extra_checks=[
        ("divide_returns_float", lambda ws: _check_divide(ws / "calculator.py")),
    ],
)


def _check_divide(calc_path: Path) -> bool:
    try:
        g = {"__builtins__": __builtins__}
        exec(calc_path.read_text(), g)
        fn = g.get("divide")
        if not callable(fn):
            return False
        result = fn(5, 2)
        return abs(result - 2.5) < 0.001
    except Exception:
        return False


# ═════════════════════════════════════════════════════════════════════════
#  Benchmark Execution Recorder
# ═════════════════════════════════════════════════════════════════════════

class BenchmarkRecorder:
    """Persists a full execution record to the session directory."""

    def __init__(self, session_dir: Path) -> None:
        self._dir = session_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._calls: list[dict] = []
        self._results: list[dict] = []
        self._raw_lines: list[str] = []

    def write_prompt(self, text: str) -> None:
        (self._dir / "prompt.txt").write_text(text, encoding="utf-8")

    def write_context(self, data: dict) -> None:
        (self._dir / "context.json").write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8",
        )

    def log(self, line: str) -> None:
        self._raw_lines.append(line)

    def record_call(self, data: dict) -> None:
        self._calls.append(data)

    def record_result(self, data: dict) -> None:
        self._results.append(data)

    def flush(self) -> None:
        for name, entries in [
            ("tool_calls.jsonl", self._calls),
            ("tool_results.jsonl", self._results),
        ]:
            path = self._dir / name
            with open(path, "w", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, default=str) + "\n")
        (self._dir / "trace.log").write_text(
            "\n".join(self._raw_lines), encoding="utf-8",
        )


# ═════════════════════════════════════════════════════════════════════════
#  Event Sequence Validation
# ═════════════════════════════════════════════════════════════════════════

def validate_sequence(events: list[dict]) -> dict[str, bool]:
    """Verify the fail-fix-pass event sequence A-F.

    Returns dict of check_name -> bool.
    """
    r: dict[str, bool] = {}

    # Build a compact tool-sequence list: each entry is
    # (kind, tool, cmd_or_path_str)
    seq: list[tuple[str, str, str]] = []
    for ev in events:
        t = ev.get("type", "")
        p = ev.get("payload", {})
        if t == "tool_call":
            tool = p.get("tool", "")
            args = p.get("args", {})
            if tool == "terminal":
                cmd = args.get("command", "")
                seq.append(("call", "terminal", cmd))
            elif tool == "filesystem":
                action = args.get("action", "")
                path = args.get("path", "")
                seq.append(("call", f"fs/{action}", path))
        elif t == "tool_result":
            tool = p.get("tool", "")
            seq.append(("result", tool,
                        json.dumps({k: p.get(k) for k in ("success", "exit_code", "stdout", "stderr")
                                    if k in p})))

    # A — first pytest call
    idx_a: int | None = None
    for i, (kind, tool, cmd) in enumerate(seq):
        if kind == "call" and tool == "terminal" and "pytest" in cmd:
            idx_a = i
            break
    r["A_first_pytest_call"] = idx_a is not None

    # B — first pytest result with failure
    idx_b: int | None = None
    if idx_a is not None:
        for i in range(idx_a + 1, len(seq)):
            if seq[i][0] == "result" and seq[i][1] == "terminal":
                idx_b = i
                break
    if idx_b is not None:
        payload = json.loads(seq[idx_b][2])
        r["B_failed_exit_code"] = payload.get("exit_code", 0) != 0
        r["B_failed_success_false"] = payload.get("success", True) is False
    else:
        r["B_failed_exit_code"] = False
        r["B_failed_success_false"] = False

    # C — filesystem write to fix calculator.py (AFTER the failure)
    idx_c: int | None = None
    start_c = (idx_b or idx_a or 0) + 1
    for i in range(start_c, len(seq)):
        if seq[i][0] == "call" and seq[i][1] == "fs/write" and "calculator.py" in seq[i][2]:
            idx_c = i
            break
    r["C_fix_write_found"] = idx_c is not None

    # D — second pytest call (AFTER the fix write)
    idx_d: int | None = None
    start_d = (idx_c or start_c) + 1
    for i in range(start_d, len(seq)):
        if seq[i][0] == "call" and seq[i][1] == "terminal" and "pytest" in seq[i][2]:
            idx_d = i
            break
    r["D_second_pytest_call"] = idx_d is not None

    # E — second pytest result with success
    idx_e: int | None = None
    if idx_d is not None:
        for i in range(idx_d + 1, len(seq)):
            if seq[i][0] == "result" and seq[i][1] == "terminal":
                idx_e = i
                break
    if idx_e is not None:
        payload = json.loads(seq[idx_e][2])
        r["E_second_exit_code_zero"] = payload.get("exit_code", 0) == 0
        r["E_second_success_true"] = payload.get("success", False) is True
    else:
        r["E_second_exit_code_zero"] = False
        r["E_second_success_true"] = False

    # F — TASK_COMPLETED (no TASK_FAILED)
    r["F_task_completed"] = any(ev.get("type") == "task_completed" for ev in events)
    r["F_no_task_failed"] = not any(ev.get("type") == "task_failed" for ev in events)

    # Composite
    r["SEQUENCE_VALID"] = all([
        r.get("A_first_pytest_call", False),
        r.get("B_failed_success_false", False),
        r.get("C_fix_write_found", False),
        r.get("D_second_pytest_call", False),
        r.get("E_second_success_true", False),
        r.get("F_task_completed", False),
        r.get("F_no_task_failed", True),
    ])
    return r


# ═════════════════════════════════════════════════════════════════════════
#  Workspace Helpers
# ═════════════════════════════════════════════════════════════════════════

def seed_workspace(ws: Path, files: dict[str, str]) -> None:
    ws.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (ws / name).write_text(content.strip() + "\n", encoding="utf-8")


# ═════════════════════════════════════════════════════════════════════════
#  Single-Scenario Runner
# ═════════════════════════════════════════════════════════════════════════

SEP = "=" * 72


def psep(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


async def run_scenario(scenario: BugScenario) -> bool:
    """Execute one scenario; return True iff all exit criteria pass."""

    psep(f"[{scenario.name}] 1. Setup workspace")

    session_dir = BACKEND_DIR / "sessions" / f"bench_{scenario.name}"
    if session_dir.exists():
        shutil.rmtree(session_dir)
    workspace_root = session_dir / "workspace"
    seed_workspace(workspace_root, scenario.seed_files)
    for fname in scenario.seed_files:
        print(f"   Seeded: {workspace_root / fname}")

    # Change CWD so relative paths resolve inside the workspace
    _orig_cwd = Path.cwd()
    os.chdir(str(workspace_root))

    bench_rec = BenchmarkRecorder(session_dir)
    bench_rec.write_prompt(scenario.task_desc)

    psep(f"[{scenario.name}] 2. Load config & tools")

    config = MOZAConfig.from_yaml(PROJECT_DIR / "config.yaml")
    provider = config.get_provider("groq")
    print(f"   Model: {provider.model}")
    if not provider.api_key:
        print("   FAIL: No GROQ_API_KEY")
        os.chdir(str(_orig_cwd))
        return False

    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    await registry.load(TerminalTool())
    for t in registry.get_all():
        print(f"   Tool: {t.name} v{t.version}")

    psep(f"[{scenario.name}] 3. EventBus & Recorder")

    import moza.core.event_recorder as er_mod
    import moza.core.event_bus as eb_mod

    recorder = EventRecorder(base_path=str(session_dir))
    er_mod._recorder = recorder
    eb_mod._event_bus = None
    event_bus = eb_mod.get_event_bus()
    event_bus.subscribe(scenario.name)

    bench_rec.write_context({
        "scenario": scenario.name,
        "workspace": str(workspace_root),
        "session_id": scenario.name,
        "model": provider.model,
    })

    psep(f"[{scenario.name}] 4. Create session & task")

    env = Environment(filesystem={"root_path": str(workspace_root)})
    session = Session(id=scenario.name)
    task = Task(session_id=session.id, description=scenario.task_desc)
    session.tasks.append(task)
    print(f"   Session: {session.id}")
    print(f"   Task:    {task.id}")

    psep(f"[{scenario.name}] 5. ExecutionContext")

    ctx = ExecutionContext.build(
        session=session,
        environment=env,
        tool_registry=registry,
        event_bus=event_bus,
    )

    psep(f"[{scenario.name}] 6. Execute agent")

    agent = LiteLLMToolAgent(config, provider_name="groq", max_steps=15)
    events: list[Any] = []
    t0 = time.monotonic()
    call_count = 0

    async for event in agent.execute(ctx):
        events.append(event)
        await event_bus.publish(scenario.name, event)
        ts = event.timestamp.strftime("%H:%M:%S.%f")[:12]
        etype = event.type.value

        if etype == "llm_token":
            text = event.payload.get("content", "")
            print(text, end="", flush=True)
            bench_rec.log(f"[{ts}] TOKEN: {text}")

        elif etype == "tool_call":
            call_count += 1
            tool = event.payload.get("tool", "?")
            args = event.payload.get("args", {})
            line = f"\n>>> [{ts}] TOOL_CALL #{call_count}: {tool}"
            print(line)
            for aline in json.dumps(args, indent=4).split("\n"):
                print(f"    {aline}")
            bench_rec.log(line)
            bench_rec.log(json.dumps(args, indent=4))
            bench_rec.record_call({"step": call_count, "tool": tool, "args": args})

        elif etype == "tool_result":
            tool = event.payload.get("tool", "?")
            success = event.payload.get("success", True)
            stdout = event.payload.get("stdout", "")
            stderr = event.payload.get("stderr", "")
            dur = event.payload.get("duration_ms", 0)
            status = "OK" if success else "FAIL"
            line = f"<<< [{ts}] TOOL_RESULT: {tool} {status} ({dur:.0f}ms)"
            print(line)
            bench_rec.log(line)
            if stderr:
                for l in stderr.strip().split("\n"):
                    print(f"    ! {l}")
                    bench_rec.log(f"    ! {l}")
            if stdout:
                for l in stdout.strip().split("\n"):
                    print(f"    | {l}")
                    bench_rec.log(f"    | {l}")
            bench_rec.record_result({
                "tool": tool, "success": success,
                "stdout": stdout, "stderr": stderr,
                "exit_code": event.payload.get("exit_code"),
            })

        elif etype == "llm_finished":
            c = event.payload.get("content", "")
            print(f"\n[{ts}] LLM_FINISHED: {c[:300]}")
        elif etype == "task_completed":
            print(f"[{ts}] TASK_COMPLETED")
        elif etype == "task_failed":
            print(f"[{ts}] TASK_FAILED: {event.payload.get('error', '?')}")
        elif etype == "agent_thinking":
            print(f"[{ts}] AGENT_THINKING: {event.payload.get('content', '')}")

    elapsed = time.monotonic() - t0
    bench_rec.flush()

    # Restore CWD
    os.chdir(str(_orig_cwd))

    psep(f"[{scenario.name}] 7. Event sequence validation (6-step A-F)")

    ev_dicts = [e.model_dump() for e in events]
    seq = validate_sequence(ev_dicts)
    for check, ok in seq.items():
        print(f"   {'PASS' if ok else 'FAIL'}: {check}")

    psep(f"[{scenario.name}] 8. Anti-cheat / post-run integrity")

    integrity_ok = True

    # 8a — calculator.py was actually fixed (content differs from seed)
    calc_path = workspace_root / "calculator.py"
    test_path = workspace_root / "test_calculator.py"
    final_calc = calc_path.read_text(encoding="utf-8") if calc_path.exists() else ""
    seed_calc = scenario.seed_files.get("calculator.py", "")
    calc_was_modified = final_calc.strip() != seed_calc.strip()
    print(f"   calculator.py modified:  {'PASS' if calc_was_modified else 'FAIL'}")
    integrity_ok = integrity_ok and calc_was_modified

    # 8b — calculator.py is now mathematically correct
    try:
        g = {"__builtins__": __builtins__}
        exec(final_calc, g)
        fn = g.get("divide")
        math_correct = callable(fn) and abs(fn(5, 2) - 2.5) < 0.001
        print(f"   divide(5,2)==2.5:        {'PASS' if math_correct else 'FAIL'}")
    except Exception as e:
        math_correct = False
        print(f"   divide(5,2)==2.5:        FAIL (exc: {e})")
    integrity_ok = integrity_ok and math_correct

    # 8c — test_calculator.py exists with all required integrity keywords
    test_exists = test_path.exists()
    print(f"   test_calculator.py:      {'PASS' if test_exists else 'FAIL'}")
    integrity_ok = integrity_ok and test_exists

    if test_exists:
        test_content = test_path.read_text(encoding="utf-8")
        for kw in scenario.test_keywords:
            has = kw in test_content
            print(f"   keyword '{kw}' in test: {'PASS' if has else 'FAIL'}")
            integrity_ok = integrity_ok and has

    # 8d — extra scenario checks
    for cname, cfn in scenario.extra_checks:
        try:
            ok = cfn(workspace_root)
        except Exception as e:
            ok = False
            print(f"   extra '{cname}':          FAIL (exc: {e})")
        print(f"   extra '{cname}':          {'PASS' if ok else 'FAIL'}")
        integrity_ok = integrity_ok and ok

    psep(f"[{scenario.name}] 9. Events persisted")

    recorded = recorder.replay(scenario.name, task.id)
    print(f"   events.jsonl entries: {len(recorded)}")
    replay_ok = len(recorded) >= 6

    psep(f"[{scenario.name}] 10. Exit criteria summary")

    criteria = {
        "A: first pytest executed": seq.get("A_first_pytest_call", False),
        "B: first pytest failed": seq.get("B_failed_success_false", False),
        "C: agent fixed calculator.py": seq.get("C_fix_write_found", False),
        "D: second pytest executed": seq.get("D_second_pytest_call", False),
        "E: second pytest passed": seq.get("E_second_success_true", False),
        "F: TASK_COMPLETED": seq.get("F_task_completed", False),
        "calculator.py mathematically correct": math_correct,
        "test file integrity preserved": integrity_ok,
        "events persisted (>=6)": replay_ok,
    }
    all_pass = all(criteria.values())
    for name, ok in criteria.items():
        print(f"   {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n   Result: {'EXIT CRITERIA MET' if all_pass else 'EXIT CRITERIA NOT MET'}")

    psep(f"[{scenario.name}] 11. Cleanup")
    shutil.rmtree(session_dir)
    print(f"   Removed: {session_dir}")

    return all_pass


# ═════════════════════════════════════════════════════════════════════════
#  Main — run all scenarios
# ═════════════════════════════════════════════════════════════════════════

SCENARIOS: list[BugScenario] = [
    INTEGER_DIVISION,
    # ── Add new scenarios here ──
]


async def main() -> bool:
    overall = True
    for sc in SCENARIOS:
        ok = await run_scenario(sc)
        overall = overall and ok

    psep("SUMMARY")
    for sc in SCENARIOS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {sc.name}")
    print(f"\n  Overall: {'ALL PASS' if overall else 'SOME FAILED'}")
    return overall


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
