import os
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import Field

from moza.tools.registry import BaseTool, ToolParameter


class FilesystemTool(BaseTool):
    """
    Filesystem operations: read, write, list directory contents.

    Write operations are marked destructive and require user confirmation.
    """
    name: str = "filesystem"
    description: str = "Read, write, and list files in the workspace."
    version: str = "1.0.0"
    parameters: list[ToolParameter] = Field(default_factory=lambda: [
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
    ])
    returns: str = "File content, directory listing, or write confirmation."
    requires_confirmation: bool = True
    is_destructive: bool = True
    capabilities: list[str] = Field(default_factory=lambda: [
        "read_file",
        "write_file",
        "list_dir",
    ])

    async def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action")
        path = kwargs.get("path")
        content = kwargs.get("content")

        if not action or not path:
            return {"error": "'action' and 'path' are required."}

        target = Path(path)

        if action == "read":
            if not target.exists():
                return {"error": f"Path does not exist: {path}"}
            if not target.is_file():
                return {"error": f"Path is not a file: {path}"}
            logger.debug(f"FilesystemTool: read {path}")
            return {"content": target.read_text(encoding="utf-8"), "path": path}

        if action == "write":
            if not content:
                return {"error": "'content' is required for write action."}
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            logger.warning(f"FilesystemTool: wrote {path} ({len(content)} chars)")
            return {
                "status": "written",
                "path": path,
                "bytes": len(content),
            }

        if action == "list":
            if not target.exists():
                return {"error": f"Path does not exist: {path}"}
            if not target.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            entries = []
            for entry in sorted(target.iterdir()):
                entries.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else None,
                })
            logger.debug(f"FilesystemTool: listed {path} ({len(entries)} entries)")
            return {"entries": entries, "path": path}

        return {"error": f"Unknown action: {action}"}
