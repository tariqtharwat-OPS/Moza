import asyncio
import os
from typing import Any

from loguru import logger
from pydantic import Field

from moza.tools.registry import BaseTool, ToolParameter


class TerminalTool(BaseTool):
    """
    Execute shell commands in the workspace.

    Marked destructive and requires user confirmation because shell commands
    can modify files or state outside the expected scope.
    """
    name: str = "terminal"
    description: str = "Execute shell commands in the workspace."
    version: str = "1.0.0"
    parameters: list[ToolParameter] = Field(default_factory=lambda: [
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
    ])
    returns: str = "stdout, stderr, exit_code"
    requires_confirmation: bool = True
    is_destructive: bool = True
    capabilities: list[str] = Field(default_factory=lambda: ["run_command"])

    async def execute(self, **kwargs: Any) -> Any:
        command = kwargs.get("command")
        cwd = kwargs.get("cwd")
        timeout = int(kwargs.get("timeout", 30))

        if not command:
            return {"error": "'command' is required."}

        logger.warning(f"TerminalTool: exec {command} (timeout={timeout}s)")

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            return {
                "command": command,
                "exit_code": proc.returncode,
                "stdout": stdout_bytes.decode("utf-8", errors="replace"),
                "stderr": stderr_bytes.decode("utf-8", errors="replace"),
            }
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {
                "error": f"Command timed out after {timeout}s",
                "command": command,
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "error": f"Command failed: {e}",
                "command": command,
                "exit_code": -1,
            }
