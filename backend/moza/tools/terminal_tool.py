import asyncio
import subprocess
import sys
import time
from typing import Any

from loguru import logger

from moza.core.models import ToolResultPayload
from moza.tools.registry import BaseTool, ToolParameter


class TerminalTool(BaseTool):
    """
    Execute shell commands in the workspace.

    Purely stateless: takes a command, returns stdout/stderr/exit_code.
    Knows nothing about xterm.js or any UI.
    """
    name: str = "terminal"
    description: str = "Execute shell commands in the workspace."
    version: str = "1.0.0"
    parameters: list[ToolParameter] = [
        ToolParameter(
            name="command",
            type="string",
            description="Shell command to execute",
            required=True,
        ),
        ToolParameter(
            name="cwd",
            type="string",
            description="Working directory (defaults to workspace root)",
            required=False,
        ),
        ToolParameter(
            name="timeout",
            type="integer",
            description="Timeout in seconds (default 30)",
            required=False,
        ),
    ]
    returns: str = "stdout, stderr, exit_code"
    requires_confirmation: bool = True
    is_destructive: bool = True
    capabilities: list[str] = ["run_command"]

    def __init__(self) -> None:
        self._active_process: asyncio.subprocess.Process | None = None

    async def execute(self, **kwargs: Any) -> Any:
        start = time.monotonic()
        command = kwargs.get("command")
        cwd = kwargs.get("cwd")
        timeout = int(kwargs.get("timeout", 30))

        if not command:
            return ToolResultPayload.error(
                "'command' is required.",
                duration_ms=(time.monotonic() - start) * 1000,
            ).model_dump()

        logger.warning(f"TerminalTool: exec {command} (timeout={timeout}s)")
        self._active_process = None

        try:
            try:
                # Attempt async subprocess (may raise NotImplementedError on some Windows configs)
                result = await self._run_async(command, cwd, timeout, start)
            except NotImplementedError:
                # Fallback: use synchronous subprocess in executor
                logger.warning("TerminalTool: async subprocess not supported, falling back to sync subprocess")
                result = await self._run_sync(command, cwd, timeout, start)
            return result

        except asyncio.TimeoutError:
            elapsed = (time.monotonic() - start) * 1000
            try:
                if self._active_process:
                    self._active_process.kill()
            except Exception:
                pass
            finally:
                self._active_process = None
            return ToolResultPayload(
                success=False,
                duration_ms=elapsed,
                exit_code=-1,
                stderr=f"Command timed out after {timeout}s",
            ).model_dump()

        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            err_detail = f"{type(e).__name__}: {e}" if str(e) else f"{type(e).__name__} (no message)"
            logger.error(f"TerminalTool: command failed — {err_detail}")
            return ToolResultPayload(
                success=False,
                duration_ms=elapsed,
                exit_code=-1,
                stderr=err_detail,
            ).model_dump()

        finally:
            self._active_process = None

    async def _run_async(self, command: str, cwd: str | None, timeout: int, start: float) -> dict:
        shell_cmd = ["cmd", "/c", command] if sys.platform == "win32" else ["sh", "-c", command]
        proc = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        self._active_process = proc
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        elapsed = (time.monotonic() - start) * 1000
        return ToolResultPayload(
            success=proc.returncode == 0,
            duration_ms=elapsed,
            exit_code=proc.returncode or 0,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
        ).model_dump()

    async def _run_sync(self, command: str, cwd: str | None, timeout: int, start: float) -> dict:
        """Fallback: run command synchronously in a thread via asyncio executor."""
        loop = asyncio.get_running_loop()

        def _run():
            shell = ["cmd", "/c", command] if sys.platform == "win32" else ["sh", "-c", command]
            result = subprocess.run(
                shell,
                capture_output=True,
                cwd=cwd,
                timeout=timeout,
            )
            return result

        proc_result = await loop.run_in_executor(None, _run)
        elapsed = (time.monotonic() - start) * 1000
        return ToolResultPayload(
            success=proc_result.returncode == 0,
            duration_ms=elapsed,
            exit_code=proc_result.returncode or 0,
            stdout=proc_result.stdout.decode("utf-8", errors="replace"),
            stderr=proc_result.stderr.decode("utf-8", errors="replace"),
        ).model_dump()

    async def cleanup(self) -> None:
        if self._active_process and self._active_process.returncode is None:
            logger.warning("TerminalTool: killing active subprocess during cleanup")
            try:
                self._active_process.kill()
            except Exception:
                pass
            self._active_process = None
