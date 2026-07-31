from fastapi import APIRouter, Request

router = APIRouter(prefix="/v1")

@router.get("/orchestrator/info")
async def get_orchestrator_info(request: Request):
    """Get current orchestrator status and provider information from the running router."""
    router_instance = getattr(request.app.state, "router", None)
    if router_instance is None:
        return {"enabled": False, "error": "Router not initialized"}
    try:
        summary = router_instance.summary()
        orch = summary.get("orchestrator", {})
        raw_provider = orch.get("current_provider", "")
        raw_model = orch.get("current_model", "unknown")
        # If provider contains "/model" suffix, split it
        if "/" in raw_provider:
            parts = raw_provider.split("/", 1)
            provider_name = parts[0]
            if raw_model == "unknown":
                raw_model = parts[1]
        else:
            provider_name = raw_provider if raw_provider else "unknown"
        return {
            "enabled": True,
            "current_provider": provider_name,
            "current_model": raw_model,
            "current_rank": orch.get("current_rank", 0),
            "success_rate": orch.get("success_rate", 0),
            "dead_providers": orch.get("dead_providers", []),
            "total_providers": orch.get("total_providers", orch.get("providers", 7)),
            "total_models": orch.get("total_models", 19),
        }
    except Exception as e:
        return {"enabled": False, "error": str(e)}