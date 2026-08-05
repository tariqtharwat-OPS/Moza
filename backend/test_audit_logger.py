import sys
import os
sys.path.insert(0, r'D:\Moza\backend')

from moza.core.audit_logger import get_audit_logger

# Test audit logger
logger = get_audit_logger()

# Emit a test event
logger.emit(
    event_type="test_event",
    details={"message": "Audit logger test successful"},
    metadata={"test": "true"}
)

print("Test event emitted. Check audit_log.jsonl for the entry.")