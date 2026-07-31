#!/usr/bin/env python
"""MOZA Launcher — one-click startup of backend, frontend, and Chrome."""

import subprocess
import sys
import time
import os
import socket
import shutil
import webbrowser


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
BACKEND_PORT = 8001
FRONTEND_PORT = 3000


def resolve_python() -> str:
    """Return a real Python interpreter path.

    When running as a frozen PyInstaller exe, sys.executable points at the
    launcher itself — NOT python — so we must locate a real interpreter.
    """
    if not getattr(sys, "frozen", False):
        return sys.executable
    for candidate in (shutil.which("python"), shutil.which("python3"), shutil.which("py")):
        if candidate:
            return candidate
    return sys.executable


def resolve_python_prefix() -> list[str]:
    """Return the argv prefix needed to run a module with the resolved interpreter."""
    interp = resolve_python()
    base = os.path.basename(interp).lower()
    if base in ("py", "py.exe"):
        return [interp, "-3"]
    return [interp]


def port_free(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
        return True
    except OSError:
        return False


def kill_port(port: int) -> None:
    import subprocess as sp
    out = sp.run(
        f'netstat -ano | findstr :{port} | findstr LISTENING',
        capture_output=True, text=True, shell=True
    )
    for line in out.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) >= 5:
            try:
                pid = int(parts[-1])
                subprocess.call(["taskkill", "/F", "/PID", str(pid)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except ValueError:
                pass


def wait_for_port(port: int, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        if result == 0:
            return True
        time.sleep(1)
    return False


def _run() -> bool:
    """Start servers, wait, open Chrome, block until user stops. Returns True on clean stop."""
    backend_proc = None
    frontend_proc = None
    ok = False
    try:
        print("=" * 50)
        print("  MOZA Launcher")
        print("=" * 50)

        # ── Port checks ──────────────────────────────────────────────────────
        for port, name in [(BACKEND_PORT, "Backend"), (FRONTEND_PORT, "Frontend")]:
            if not port_free(port):
                print(f"\n[!] Port {port} ({name}) is already in use.")
                try:
                    ans = input(f"    Kill existing process and continue? [Y/n] ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    ans = "n"
                if ans in ("", "y", "yes"):
                    kill_port(port)
                    time.sleep(2)
                    if not port_free(port):
                        print(f"    Could not free port {port}. Exiting.")
                        return False
                else:
                    print(f"    Cannot continue. Port {port} is busy.")
                    return False

        # ── Start backend ─────────────────────────────────────────────────────
        python_prefix = resolve_python_prefix()
        print("\n[*] Starting backend (port 8001)...")
        backend_proc = subprocess.Popen(
            [*python_prefix, "-m", "uvicorn", "moza.main:app",
             "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
            cwd=BACKEND_DIR,
        )
        print(f"    Backend PID: {backend_proc.pid}")

        print("    Waiting for backend...", end="", flush=True)
        if wait_for_port(BACKEND_PORT, timeout=20):
            print(" ready!")
        else:
            print("  TIMEOUT")
            print("    Backend may still be starting. Check the logs above for errors.")
            return False

        # ── Start frontend ────────────────────────────────────────────────────
        print("\n[*] Starting frontend (port 3000)...")
        frontend_proc = subprocess.Popen(
            ["cmd", "/c", "npm run dev"],
            cwd=FRONTEND_DIR,
        )
        print(f"    Frontend PID: {frontend_proc.pid}")

        print("    Waiting for frontend...", end="", flush=True)
        if wait_for_port(FRONTEND_PORT, timeout=35):
            print(" ready!")
        else:
            print("  [!] Timeout")
            print("    Next.js may need more time. Check the logs above.")
            return False

        # ── Open Chrome ──────────────────────────────────────────────────────
        url = f"http://localhost:{FRONTEND_PORT}"
        print(f"\n[*] Opening Chrome -> {url}")
        webbrowser.open(url)

        print("\n" + "=" * 50)
        print("  MOZA is running!")
        print(f"  Backend:  http://localhost:{BACKEND_PORT}/v1/orchestrator/info")
        print(f"  Frontend: {url}")
        print("  Live logs appear in this window. Press ENTER to stop all servers.")
        print("=" * 50)
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass

        # ── Shutdown ─────────────────────────────────────────────────────────
        print("\n[*] Shutting down...")
        for proc in (backend_proc, frontend_proc):
            if proc is None or proc.poll() is not None:
                continue
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("    Servers stopped. Goodbye!")
        ok = True
    finally:
        # On failure, stop anything we started.
        if not ok:
            for proc in (backend_proc, frontend_proc):
                if proc is not None and proc.poll() is None:
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    except Exception:
                        pass
    return ok


def main() -> None:
    try:
        _run()
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user.")
    except Exception as e:
        print(f"\n[!] Launcher error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "=" * 50)
        print("  Launcher exiting.")
        print("  Press ENTER to close this window ...")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    main()