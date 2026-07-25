"""Minimal launcher for MOZA backend (used by Start-Process)."""
import uvicorn
uvicorn.run("moza.main:app", host="0.0.0.0", port=8000, log_level="info")
