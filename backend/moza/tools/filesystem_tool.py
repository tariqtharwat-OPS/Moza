import time
from pathlib import Path
from typing import Any

from loguru import logger

from moza.core.models import ToolResultPayload
from moza.tools.registry import BaseTool, ToolParameter


class FilesystemTool(BaseTool):
    name: str = "filesystem"
    description: str = "Read, write, and list files in the workspace."
    version: str = "1.0.0"
    parameters: list[ToolParameter] = [
        ToolParameter(
            name="action",
            type="enum",
            description="One of: read | write | list",
            required=True,
        ),
        ToolParameter(
            name="path",
            type="string",
            description="Absolute or workspace-relative path",
            required=True,
        ),
        ToolParameter(
            name="content",
            type="string",
            description="File content (required for 'write' action)",
            required=False,
        ),
    ]
    returns: str = "File content, directory listing, or write confirmation."
    requires_confirmation: bool = True
    is_destructive: bool = True
    capabilities: list[str] = [
        "read_file",
        "write_file",
        "list_dir",
    ]

    async def execute(self, **kwargs: Any) -> Any:
        start = time.monotonic()
        action = kwargs.get("action")
        path = kwargs.get("path")
        content = kwargs.get("content")

        if not action or not path:
            return ToolResultPayload.error(
                "'action' and 'path' are required.",
                duration_ms=(time.monotonic() - start) * 1000,
            ).model_dump()

        target = Path(path)

        if action == "read":
            if not target.exists():
                return ToolResultPayload.error(
                    f"Path does not exist: {path}",
                    duration_ms=(time.monotonic() - start) * 1000,
                ).model_dump()
            if not target.is_file():
                return ToolResultPayload.error(
                    f"Error: '{path}' is a directory, not a file. To read a file, provide a valid file path (e.g. 'readme.txt'). To list directory contents, use action='list' instead.",
                    duration_ms=(time.monotonic() - start) * 1000,
                ).model_dump()
            text = target.read_text(encoding="utf-8")
            elapsed = (time.monotonic() - start) * 1000
            logger.debug(f"FilesystemTool: read {path} ({len(text)} chars, {elapsed:.0f}ms)")
            return ToolResultPayload.ok(
                stdout=text,
                duration_ms=elapsed,
                metadata={"path": path, "bytes": len(text)},
            ).model_dump()

        if action == "write":
            if not content:
                return ToolResultPayload.error(
                    "'content' is required for write action.",
                    duration_ms=(time.monotonic() - start) * 1000,
                ).model_dump()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            elapsed = (time.monotonic() - start) * 1000
            logger.warning(f"FilesystemTool: wrote {path} ({len(content)} chars, {elapsed:.0f}ms)")
            return ToolResultPayload.ok(
                stdout=f"Written {len(content)} bytes to {path}",
                duration_ms=elapsed,
                metadata={"path": path, "bytes": len(content)},
            ).model_dump()

        if action == "list":
            if not target.exists():
                return ToolResultPayload.error(
                    f"Path does not exist: {path}",
                    duration_ms=(time.monotonic() - start) * 1000,
                ).model_dump()
            if not target.is_dir():
                return ToolResultPayload.error(
                    f"Path is not a directory: {path}",
                    duration_ms=(time.monotonic() - start) * 1000,
                ).model_dump()
            entries = []
            for entry in sorted(target.iterdir()):
                entries.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else None,
                })
            elapsed = (time.monotonic() - start) * 1000
            logger.debug(f"FilesystemTool: listed {path} ({len(entries)} entries, {elapsed:.0f}ms)")
            return ToolResultPayload.ok(
                stdout="\n".join(e["name"] for e in entries),
                duration_ms=elapsed,
                metadata={"path": path, "entries": entries, "count": len(entries)},
            ).model_dump()

        return ToolResultPayload.error(
            f"Unknown action: {action}",
            duration_ms=(time.monotonic() - start) * 1000,
        ).model_dump()
