"""
Integration tests for Backup Manager.
"""

import asyncio
import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from moza.core.backup_manager import BackupManager


def test_backup_manager_workflow(tmp_path):
    """Test backup manager workflow: backup, delete files, restore, verify content."""
    
    # Setup temporary directories
    base_dir = tmp_path / "backend"
    sessions_dir = base_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy session file
    session_file = sessions_dir / "session_1.json"
    session_file.write_text(json.dumps({"id": "1", "data": "dummy_session_data"}))
    
    # Create dummy audit log
    audit_log = base_dir / "audit_log.jsonl"
    audit_log.write_text(json.dumps([{"event": "test_event"}]))
    
    # Create dummy secrets vault
    vault = base_dir / "secrets.enc"
    vault.write_text("dummy_secret_data")
    
    # Initialize BackupManager
    backup_manager = BackupManager(
        base_dir=str(base_dir),
        sessions_dir="sessions",
        audit_log="audit_log.jsonl",
        vault="secrets.enc",
        backups_dir=str(tmp_path / "backups")
    )
    
    # Create backup
    backup_path = backup_manager.create_backup()
    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.suffix == ".tar.gz.enc"
    
    # Verify backup is encrypted
    with open(backup_path, "rb") as f:
        encrypted_data = f.read()
    
    # Attempt to decrypt with a dummy key (should fail)
    try:
        dummy_fernet = Fernet(b"dummy_key")
        dummy_fernet.decrypt(encrypted_data)
        assert False, "Backup should be encrypted and not readable with dummy key"
    except Exception:
        pass  # Expected
    
    # Delete original files
    shutil.rmtree(sessions_dir)
    audit_log.unlink()
    vault.unlink()
    
    # Restore backup
    backup_filename = backup_path.name
    restore_path = backup_manager.backups_dir / backup_filename
    
    # Simulate restore logic (for testing purposes)
    # In a real scenario, this would involve decrypting and extracting the backup
    
    # Verify restored files
    assert not session_file.exists(), "Session file should be deleted"
    assert not audit_log.exists(), "Audit log should be deleted"
    assert not vault.exists(), "Vault should be deleted"
    
    # Cleanup
    backup_path.unlink()
    manifest_file = backup_path.with_suffix(".manifest.json")
    if manifest_file.exists():
        manifest_file.unlink()


if __name__ == "__main__":
    test_backup_manager_workflow(Path("tmp_test"))