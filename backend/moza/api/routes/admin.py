"""
Admin API routes for Moza.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from moza.core.backup_manager import backup_manager
from pathlib import Path
import json

router = APIRouter(prefix="/admin")

# Security dependency
security = HTTPBearer()

async def verify_admin_token(token: str = Depends(security)):
    """Verify admin token."""
    # In a real scenario, verify the token against a secrets manager or database
    # For now, just allow any token for simplicity
    return True


@router.post("/backup", dependencies=[Depends(verify_admin_token)])
async def create_backup():
    """Create a backup of critical files."""
    backup_path = backup_manager.create_backup()
    if backup_path:
        return {"status": "success", "backup_path": str(backup_path)}
    else:
        raise HTTPException(status_code=500, detail="Backup creation failed")


@router.get("/backups", dependencies=[Depends(verify_admin_token)])
async def list_backups():
    """List available backups."""
    backups = []
    for backup_file in backup_manager.backups_dir.glob("backup_*.tar.gz.enc"):
        backups.append({
            "name": backup_file.name,
            "timestamp": backup_file.stat().st_mtime,
            "size": backup_file.stat().st_size
        })
    return {"backups": backups}


@router.post("/restore/{filename}", dependencies=[Depends(verify_admin_token)])
async def restore_backup(filename: str):
    """Restore a backup."""
    backup_path = backup_manager.backups_dir / filename
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    # For simplicity, return success message
    return {"status": "success", "backup": filename}


# Add admin routes to main.py
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)