from fastapi import APIRouter

# Initialize v1 router
v1_router = APIRouter(prefix="/v1")

# Import and include v1 routes
from moza.api.routes.chat import router as chat_router
from moza.api.routes.test_chat import router as test_chat_router
from moza.api.routes.replay import router as replay_router
from moza.api.routes.orchestrator import router as orchestrator_router
from moza.api.routes.admin import router as admin_router

v1_router.include_router(chat_router)
v1_router.include_router(test_chat_router)
v1_router.include_router(replay_router)
v1_router.include_router(orchestrator_router)
v1_router.include_router(admin_router)

# Initialize v2 router
v2_router = APIRouter(prefix="/v2")

# Import and include v2 routes
from moza.api.routes.v2_example import router as v2_example_router

v2_router.include_router(v2_example_router)

__all__ = ["v1_router", "v2_router"]