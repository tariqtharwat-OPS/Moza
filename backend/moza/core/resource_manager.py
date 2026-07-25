from dataclasses import dataclass, field


@dataclass
class ResourceManager:
    """
    Manages workspace resources: git state, file watching, and vector indexing.

    Currently a STUB — placeholder methods to be implemented when
    real Git/watchers/embeddings are integrated.
    """
    workspace_path: str = ""
    git_branch: str | None = None
    _watchers: dict = field(default_factory=dict)
    _index: dict = field(default_factory=dict)

    async def git_status(self) -> dict:
        """Returns current git status of the workspace."""
        return {
            "branch": self.git_branch,
            "modified": [],
            "untracked": [],
            "ahead_by": 0,
            "behind_by": 0,
        }

    async def file_watcher(self, event_type: str, path: str | None = None) -> dict:
        """
        Subscribes/watches for file changes in workspace.
        event_type: 'start' | 'stop' | 'status'
        """
        if event_type == "start":
            self._watchers[path or "*"] = True
            return {"status": "watching", "path": path}
        elif event_type == "stop":
            self._watchers.pop(path or "*", None)
            return {"status": "stopped", "path": path}
        return {"status": "idle", "active_watchers": len(self._watchers)}

    async def vector_index(self, path: str) -> dict:
        """Index or query a file in the vector store."""
        return {
            "status": "stub",
            "path": path,
            "message": "Vector indexing not yet implemented.",
        }

    def to_metadata(self) -> dict:
        return {
            "path": self.workspace_path,
            "branch": self.git_branch,
            "watchers": len(self._watchers),
        }
