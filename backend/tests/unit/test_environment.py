import pytest
from moza.core.models import Environment, Session, Workspace


class TestEnvironmentSubDomains:
    def test_all_six_subdomains_accessible(self):
        env = Environment()
        assert env.filesystem is not None
        assert env.terminal is not None
        assert env.browser is not None
        assert env.desktop is not None
        assert env.secrets == {}
        assert env.memory == {}

    def test_filesystem_subdomain(self):
        env = Environment(filesystem={"root_path": "/test", "git_branch": "main"})
        assert env.filesystem.root_path == "/test"
        assert env.filesystem.git_branch == "main"

    def test_terminal_subdomain(self):
        env = Environment(terminal={"cwd": "/home", "shell_type": "powershell"})
        assert env.terminal.cwd == "/home"
        assert env.terminal.shell_type == "powershell"

    def test_browser_subdomain(self):
        env = Environment(browser={"headless_mode": False})
        assert env.browser.headless_mode is False
        assert env.browser.active_tabs == []

    def test_desktop_subdomain(self):
        env = Environment(desktop={"clipboard": "hello"})
        assert env.desktop.clipboard == "hello"

    def test_secrets_store(self):
        env = Environment(secrets={"API_KEY": "abc123"})
        assert env.secrets["API_KEY"] == "abc123"

    def test_memory_store(self):
        env = Environment(memory={"conversation": ["hi", "bye"]})
        assert env.memory["conversation"] == ["hi", "bye"]

    def test_subdomains_independent(self):
        env = Environment()
        env.filesystem.root_path = "/a"
        env.terminal.cwd = "/b"
        assert env.filesystem.root_path == "/a"
        assert env.terminal.cwd == "/b"


class TestWorkspaceBackwardCompat:
    def test_workspace_is_environment(self):
        ws = Workspace()
        assert isinstance(ws, Environment)

    def test_workspace_root_path_maps_to_filesystem(self):
        ws = Workspace(root_path="/legacy")
        assert ws.filesystem.root_path == "/legacy"

    def test_workspace_bridge_in_session(self):
        env = Environment(filesystem={"root_path": "/bridge"})
        session = Session(environment=env)
        assert session.environment.filesystem.root_path == "/bridge"
        assert session.workspace.filesystem.root_path == "/bridge"
        assert session.workspace is session.environment

    def test_session_default_environment(self):
        session = Session()
        assert isinstance(session.environment, Environment)
        assert session.environment.id != ""

    def test_workspace_constructor_backward_compat(self):
        ws = Workspace(root_path="/old", git_branch="feature-x")
        assert ws.filesystem.root_path == "/old"
        assert ws.filesystem.git_branch == "feature-x"


class TestEnvironmentResourceManager:
    def test_ensure_resource_manager(self):
        env = Environment(filesystem={"root_path": "/test"})
        rm = env.ensure_resource_manager()
        assert rm is not None
        assert rm is env.resource_manager
        assert rm.workspace_path == "/test"

    def test_ensure_resource_manager_idempotent(self):
        env = Environment()
        rm1 = env.ensure_resource_manager()
        rm2 = env.ensure_resource_manager()
        assert rm1 is rm2

    def test_resource_manager_excluded_from_serialization(self):
        env = Environment()
        env.ensure_resource_manager()
        d = env.model_dump()
        assert "resource_manager" not in d


class TestEnvironmentSerialization:
    def test_round_trip(self):
        env = Environment(
            filesystem={"root_path": "/project"},
            terminal={"cwd": "/project/src"},
            secrets={"TOKEN": "xyz"},
            memory={"key": "val"},
        )
        d = env.model_dump()
        restored = Environment(**d)
        assert restored.filesystem.root_path == "/project"
        assert restored.terminal.cwd == "/project/src"
        assert restored.secrets["TOKEN"] == "xyz"
        assert restored.memory["key"] == "val"

    def test_environment_in_session_round_trip(self):
        env = Environment(secrets={"KEY": "VAL"})
        session = Session(environment=env)
        d = session.model_dump()
        restored = Session(**d)
        assert restored.environment.secrets["KEY"] == "VAL"
