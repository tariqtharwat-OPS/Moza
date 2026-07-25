import asyncio
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
            proc = await asyncio.create_subprocess_shell(
                command,
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
            return ToolResultPayload(
                success=False,
                duration_ms=elapsed,
                exit_code=-1,
                stderr=f"Command failed: {e}",
            ).model_dump()

        finally:
            self._active_process = None

    async def cleanup(self) -> None:
        if self._active_process and self._active_process.returncode is None:
            logger.warning("TerminalTool: killing active subprocess during cleanup")
            try:
                self._active_process.kill()
            except Exception:
                pass
            self._active_process = None
