import asyncio
import json
from pathlib import Path

from moza.core.context import ExecutionContext


class ContextBuilder:
    """
    Builds a rich snapshot of the current environment for LLM prompt injection.

    Seven sections:
      1. Workspace Tree  — directory structure (2-level depth)
      2. Current Directory
      3. Git Status       — clean / modified files / not a repo
      4. Recent Events    — last 5 events from execution_history
      5. Current Task     — the active task description
      6. Available Tools  — from ToolRegistry
      7. Current Artifacts
    """

    MAX_TREE_DEPTH = 2
    MAX_EVENTS = 5

    # ── public entry point ────────────────────────────────────────────────

    @classmethod
    async def build_context(cls, context: ExecutionContext) -> str:
        sections = [
            cls._section("Workspace Tree", await cls._get_workspace_tree(context)),
            cls._section("Current Directory", cls._get_current_dir(context)),
            cls._section("Git Status", await cls._get_git_status(context)),
            cls._section("Recent Events", cls._get_recent_events(context)),
            cls._section("Current Task", cls._get_current_task(context)),
            cls._section("Available Tools", cls._get_available_tools(context)),
            cls._section("Current Artifacts", cls._get_current_artifacts(context)),
        ]
        return "\n\n".join(sections)

    # ── formatting helpers ────────────────────────────────────────────────

    @staticmethod
    def _section(title: str, body: str) -> str:
        return f"[{title}]\n{body}"

    # ── workspace tree ────────────────────────────────────────────────────

    @classmethod
    async def _get_workspace_tree(cls, context: ExecutionContext) -> str:
        root = context.environment.filesystem.root_path
        if not root:
            return "(no workspace root set)"
        path = Path(root)
        if not path.exists():
            return f"Path does not exist: {root}"

        lines: list[str] = []

        async def _walk(dir_path: Path, depth: int = 0) -> None:
            if depth > cls.MAX_TREE_DEPTH:
                return
            try:
                entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except PermissionError:
                lines.append("  " * depth + "[permission denied]")
                return
            for entry in entries:
                if entry.name.startswith(".") or entry.name.startswith("__"):
                    continue
                indent = "  " * depth
                if entry.is_dir():
                    lines.append(f"{indent}{entry.name}/")
                    await _walk(entry, depth + 1)
                else:
                    try:
                        sz = entry.stat().st_size
                        lines.append(f"{indent}{entry.name} ({sz} bytes)")
                    except OSError:
                        lines.append(f"{indent}{entry.name}")

        await _walk(path)
        return "\n".join(lines) if lines else "(empty directory)"

    # ── current directory ─────────────────────────────────────────────────

    @staticmethod
    def _get_current_dir(context: ExecutionContext) -> str:
        return context.environment.filesystem.root_path or "(not set)"

    # ── git status ────────────────────────────────────────────────────────

    @staticmethod
    async def _get_git_status(context: ExecutionContext) -> str:
        root = context.environment.filesystem.root_path
        if not root:
            return "(no workspace root)"
        git_dir = Path(root) / ".git"
        if not git_dir.exists():
            return "Not a git repository"
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "status", "--short",
                cwd=root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            if proc.returncode != 0:
                return f"git error: {stderr.decode().strip()}"
            output = stdout.decode().strip()
            return output if output else "Clean — no changes"
        except FileNotFoundError:
            return "Git not installed"
        except asyncio.TimeoutError:
            return "git status timed out"
        except Exception as e:
            return f"git unavailable: {e}"

    # ── recent events ─────────────────────────────────────────────────────

    @staticmethod
    def _get_recent_events(context: ExecutionContext) -> str:
        history = context.session.execution_history
        if not history:
            return "(no events yet)"
        recent = history[-ContextBuilder.MAX_EVENTS:]
        parts: list[str] = []
        for e in recent:
            ts = e.timestamp.strftime("%H:%M:%S")
            payload_preview = json.dumps(e.payload)[:120]
            parts.append(f"  [{ts}] {e.type.value}: {payload_preview}")
        return "\n".join(parts)

    # ── current task ──────────────────────────────────────────────────────

    @staticmethod
    def _get_current_task(context: ExecutionContext) -> str:
        if context.session.tasks:
            return context.session.tasks[-1].description
        return "(no task)"

    # ── available tools ───────────────────────────────────────────────────

    @staticmethod
    def _get_available_tools(context: ExecutionContext) -> str:
        tools = context.tool_registry.get_all()
        if not tools:
            return "(no tools registered)"
        lines: list[str] = []
        for t in tools:
            caps = ", ".join(t.capabilities) if t.capabilities else "-"
            lines.append(f"  - {t.name}: {t.description} [{caps}]")
        return "\n".join(lines)

    # ── artifacts ─────────────────────────────────────────────────────────

    @staticmethod
    def _get_current_artifacts(context: ExecutionContext) -> str:
        artifacts = context.session.artifacts
        if not artifacts:
            return "(no artifacts)"
        lines: list[str] = []
        for a in artifacts:
            lines.append(f"  - {a.type.value}: {a.path} (v{a.version})")
        return "\n".join(lines)
