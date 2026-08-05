import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from moza.config.models import MOZAConfig
from moza.gateway.interfaces import LLMProvider
from moza.gateway.litellm_adapter import LiteLLMAdapter
from moza.gateway.router import LLMRouter
from moza.tools.browser_tool import BrowserTool
from moza.tools.filesystem_tool import FilesystemTool
from moza.tools.registry import get_tool_registry
from moza.tools.terminal_tool import TerminalTool
from moza.plugins import PluginManager
from moza.plugins.registry import get_plugin_registry
from moza.core.constitution import load_constitution

# Windows asyncio subprocess support (required for Playwright browser launch)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_DIR = _BACKEND_DIR.parent

app = FastAPI(title="MOZA Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3004",
        "http://127.0.0.1:3005",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class AppState:
    config: MOZAConfig
    llm: LLMProvider
    constitution: dict


app_state: AppState | None = None


@app.on_event("startup")
async def startup():
    global app_state
    
    # Initialize audit logger
    from moza.core.audit_logger import get_audit_logger
    audit_logger = get_audit_logger()
    
    # Emit startup event
    audit_logger.emit(
        event_type="system_startup",
        details={"version": "0.1.0", "backend_path": str(_BACKEND_DIR)}
    )
    
    # ADR-007 Phase 2: Auto-migrate .env keys to encrypted vault (non-fatal).
    try:
        from moza.core.secrets_manager import SecretsManager
        from moza.core.secrets_migration import SecretsMigration

        secrets_manager = SecretsManager(str(_BACKEND_DIR / "secrets.enc"))
        secrets_manager.initialize()
        migration = SecretsMigration(secrets_manager, env_path=str(_BACKEND_DIR / ".env"))
        summary = migration.run_full_migration(comment_out=True)
        if summary["migrated"] > 0:
            logger.info(
                f"Secrets migrated: {summary['migrated']} keys moved to vault, "
                f"{summary['commented_out']} commented in .env"
            )
        elif summary["skipped"] > 0:
            logger.info(f"Secrets migration: {summary['skipped']} keys already in vault")
        elif summary["keys_found"] > 0:
            logger.info(f"Secrets migration: {summary['keys_found']} keys found, none migrated")
    except Exception as e:
        logger.warning(f"Secrets migration failed (non-critical): {e}")

    config = MOZAConfig.from_yaml(_PROJECT_DIR / "config.yaml")
    logger.info(f"Loaded config with providers: {list(config.providers.keys())}")

    # Load Constitution
    constitution = load_constitution(_PROJECT_DIR / "constitution.yaml")
    logger.info(f"Loaded constitution v{constitution.get('identity', {}).get('version', 'unknown')}")

    llm: LLMProvider = LiteLLMAdapter(config)
    router = LLMRouter(config)
    app.state.config = config
    app.state.llm = llm
    app.state.router = router
    app.state.constitution = constitution
    app_state = AppState(config=config, llm=llm, constitution=constitution)

    registry = get_tool_registry()
    await registry.load(FilesystemTool())
    await registry.load(TerminalTool())
    await registry.load(BrowserTool(headless=True))
    logger.info(f"Registered {len(registry.get_all())} tools: {[t.name for t in registry.get_all()]}")

    # Plugin system — optional, failure-isolated
    _plugin_dir = _PROJECT_DIR / "plugins"
    pm = PluginManager(plugin_dirs=[str(_plugin_dir)])
    app.state.plugin_manager = pm
    plugin_registry = get_plugin_registry()
    discovered = await pm.discover_plugins()
    if discovered:
        logger.info(f"Discovered {len(discovered)} plugin(s): {[p['name'] for p in discovered]}")
        for p in discovered:
            try:
                instance = await pm.load_plugin(p)
                await plugin_registry.register_plugin(instance)
                logger.info(f"Plugin activated: {p['name']} ({p['type']})")
            except Exception as e:
                logger.error(f"Plugin activation failed: {p['name']}: {e}")
    else:
        logger.info("No plugins discovered (plugins/ directory may not exist)")
from moza.api.routes.chat import router as chat_router
from moza.core.rate_limiter import rate_limiter

# Add rate limiter middleware
app.middleware("http")(rate_limiter)

app.include_router(chat_router)

from moza.api.routes.test_chat import router as test_chat_router
app.include_router(test_chat_router)

from moza.api.routes.replay import router as replay_router
app.include_router(replay_router)

from moza.api.routes.orchestrator import router as orchestrator_router
app.include_router(orchestrator_router)

from moza.api.routes.admin import router as admin_router
app.include_router(admin_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for frontend connectivity monitoring and event streaming."""
    await websocket.accept()
    logger.info("WebSocket client connected")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")


@app.on_event("shutdown")
async def shutdown():
    pm = getattr(app.state, "plugin_manager", None)
    if pm:
        try:
            await get_plugin_registry().cleanup()
        except Exception as e:
            logger.warning(f"Plugin registry cleanup failed: {e}")
        try:
            await pm.cleanup()
        except Exception as e:
            logger.warning(f"Plugin manager cleanup failed: {e}")
    tools = get_tool_registry().get_all()
    for tool in tools:
        await get_tool_registry().unload(tool.name)
    logger.info("MOZA Backend shutting down")


if __name__ == "__main__":
    uvicorn.run("moza.main:app", host="0.0.0.0", port=8001, reload=True)
