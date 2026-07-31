#!/usr/bin/env python
"""MOZA Launcher — one-click startup of backend, frontend, and Chrome."""

import subprocess
import sys
import time
import os
import socket
import webbrowser


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
BACKEND_PORT = 8001
FRONTEND_PORT = 3000

PYTHON = sys.executable


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


def main() -> None:
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
                    return
            else:
                print(f"    Cannot continue. Port {port} is busy.")
                return

    # ── Start backend ─────────────────────────────────────────────────────
    print("\n[*] Starting backend (port 8001)...")
    backend_proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "moza.main:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
        cwd=BACKEND_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    print(f"    Backend PID: {backend_proc.pid}")

    print("    Waiting for backend...", end="", flush=True)
    if wait_for_port(BACKEND_PORT, timeout=20):
        print(" ready!")
    else:
        print("  TIMEOUT")
        print("    Backend may still be starting. Check D:\\Moza\\backend for errors.")
        backend_proc.terminate()
        return

    # ── Start frontend ────────────────────────────────────────────────────
    print("\n[*] Starting frontend (port 3000)...")
    frontend_proc = subprocess.Popen(
        ["cmd", "/c", "npm run dev"],
        cwd=FRONTEND_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    print(f"    Frontend PID: {frontend_proc.pid}")

    print("    Waiting for frontend...", end="", flush=True)
    if wait_for_port(FRONTEND_PORT, timeout=35):
        print(" ready!")
    else:
        print("  [!] Timeout")
        print("    Next.js may need more time. Close and check manually.")
        backend_proc.terminate()
        frontend_proc.terminate()
        return

    # ── Open Chrome ──────────────────────────────────────────────────────
    url = f"http://localhost:{FRONTEND_PORT}"
    print(f"\n[*] Opening Chrome -> {url}")
    webbrowser.open(url)

    print("\n" + "=" * 50)
    print("  MOZA is running!")
    print(f"  Backend:  http://localhost:{BACKEND_PORT}/v1/orchestrator/info")
    print(f"  Frontend: {url}")
    print("=" * 50)
    print("\nPress ENTER to stop all servers and exit ...")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass

    # ── Shutdown ─────────────────────────────────────────────────────────
    print("\n[*] Shutting down...")
    backend_proc.terminate()
    frontend_proc.terminate()
    try:
        backend_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        backend_proc.kill()
    try:
        frontend_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        frontend_proc.kill()
    print("    Servers stopped. Goodbye!")


if __name__ == "__main__":
    main()