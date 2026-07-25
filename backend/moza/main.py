from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI
from loguru import logger

from moza.config.models import MOZAConfig
from moza.gateway.interfaces import LLMProvider
from moza.gateway.litellm_adapter import LiteLLMAdapter
from moza.tools.filesystem_tool import FilesystemTool
from moza.tools.registry import get_tool_registry
from moza.tools.terminal_tool import TerminalTool

app = FastAPI(title="MOZA Backend", version="0.1.0")


@dataclass
class AppState:
    config: MOZAConfig
    llm: LLMProvider


app_state: AppState | None = None


@app.on_event("startup")
async def startup():
    global app_state
    config = MOZAConfig.from_yaml("config.yaml")
    logger.info(f"Loaded config with providers: {list(config.providers.keys())}")

    llm: LLMProvider = LiteLLMAdapter(config)
    app_state = AppState(config=config, llm=llm)

    registry = get_tool_registry()
    await registry.load(FilesystemTool())
    await registry.load(TerminalTool())
    logger.info(f"Registered {len(registry.get_all())} tools: {[t.name for t in registry.get_all()]}")

    from moza.api.routes.chat import router as chat_router
    app.include_router(chat_router)


@app.on_event("shutdown")
async def shutdown():
    tools = get_tool_registry().get_all()
    for tool in tools:
        await get_tool_registry().unload(tool.name)
    logger.info("MOZA Backend shutting down")


if __name__ == "__main__":
    uvicorn.run("moza.main:app", host="0.0.0.0", port=8000, reload=True)
