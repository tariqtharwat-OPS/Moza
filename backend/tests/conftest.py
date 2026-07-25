import asyncio
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def reset_globals():
    import moza.core.event_bus as eb
    import moza.core.event_recorder as er
    import moza.orchestrator.orchestrator as oc
    import moza.orchestrator.service as sv
    import moza.tools.registry as rg

    snap = {
        eb: eb._event_bus,
        er: er._recorder,
        oc: oc._orchestrator,
        sv: sv._task_service,
        rg: rg._tool_registry,
    }
    eb._event_bus = None
    er._recorder = None
    oc._orchestrator = None
    sv._task_service = None
    rg._tool_registry = None
    yield
    for mod, val in snap.items():
        try:
            for key, attr in [(eb, "_event_bus"), (er, "_recorder"), (oc, "_orchestrator"), (sv, "_task_service"), (rg, "_tool_registry")]:
                if mod is key:
                    setattr(mod, attr, val)
        except Exception:
            pass


@pytest.fixture
def tmp_recorder(tmp_path):
    from moza.core.event_recorder import EventRecorder
    return EventRecorder(base_path=str(tmp_path / "sessions"))


@pytest.fixture
def fresh_registry():
    from moza.tools.registry import ToolRegistry
    return ToolRegistry()


@pytest.fixture
def fresh_orchestrator():
    from moza.orchestrator.orchestrator import Orchestrator
    return Orchestrator()
