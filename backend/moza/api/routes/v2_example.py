from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def v2_status():
    """Example endpoint for v2 API."""
    return {"version": "2.0", "status": "experimental"}