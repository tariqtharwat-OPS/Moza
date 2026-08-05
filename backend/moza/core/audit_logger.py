"""
Audit Logger for MOZA AI Operating System.

This module provides functionality to log system events to a JSONL file.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from loguru import logger


class AuditLogger:
    """
    Persists audit events to a JSONL file.
    Each event is a single JSON line containing:
    - timestamp
    - event_type
    - event_details
    - metadata
    """
    
    def __init__(self, base_path: str = "audit_log.jsonl") -> None:
        self.base_path = Path(base_path)
        self._ensure_dir()
    
    def _ensure_dir(self) -> None:
        """Ensure the directory for the audit log exists."""
        self.base_path.parent.mkdir(parents=True, exist_ok=True)
    
    def emit(self, event_type: str, details: Dict[str, Any], metadata: Dict[str, Any] = None) -> None:
        """
        Emit an audit event.
        
        Args:
            event_type: Type of event (e.g., 'task_started', 'file_created', 'api_call')
            details: Detailed information about the event
            metadata: Additional metadata (e.g., user_id, session_id)
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
        }
        
        if metadata:
            event["metadata"] = metadata
        
        try:
            with open(self.base_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except OSError as e:
            logger.error(f"AuditLogger: failed to write to {self.base_path}: {e}")


# Initialize AuditLogger
_audit_logger: AuditLogger | None = None

def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(str(Path(__file__).resolve().parent.parent.parent / "audit_log.jsonl"))
    return _audit_logger