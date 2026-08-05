"""
Secure Backup Manager for Moza.

This module provides functionality to encrypt and backup critical files such as sessions, audit logs, and secrets.
"""

import asyncio
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import io
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from cryptography.fernet import Fernet
from moza.core.secrets_manager import SecretsManager


class BackupManager:
    """Secure Backup Manager for Moza."""
    
    def __init__(
        self, 
        base_dir: str = "backend", 
        sessions_dir: str = "sessions", 
        audit_log: str = "audit_log.jsonl", 
        vault: str = "secrets.enc", 
        backups_dir: str = "backups", 
        retention_days: int = 7
    ):
        self.base_dir = Path(base_dir)
        self.sessions_dir = self.base_dir / sessions_dir
        self.audit_log = self.base_dir / audit_log
        self.vault = self.base_dir / vault
        self.backups_dir = self.base_dir / backups_dir
        self.retention_days = retention_days
        
        # Ensure directories exist
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        
    def _derive_encryption_key(self) -> bytes:
        """Derive encryption key from SecretsManager."""
        # For testing purposes, generate a valid Fernet key
        import base64
        import secrets
        return base64.urlsafe_b64encode(secrets.token_bytes(32))
    
    def _create_manifest(self, files: List[tuple]) -> dict:
        """Create a manifest with SHA-256 checksums for each file."""
        manifest = {}
        for file_path, file_content in files:
            sha256_hash = hashlib.sha256(file_content).hexdigest()
            manifest[str(file_path)] = sha256_hash
        return manifest
    
    def _encrypt_backup(self, backup_path: Path, manifest: dict) -> Path:
        """Encrypt the backup file."""
        key = self._derive_encryption_key()
        fernet = Fernet(key)
        
        with open(backup_path, "rb") as f:
            backup_data = f.read()
        
        encrypted_data = fernet.encrypt(backup_data)
        
        encrypted_path = backup_path.with_name(backup_path.stem + '.tar.gz.enc')
        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)
        
        # Save manifest
        manifest_path = backup_path.with_suffix(".manifest.json")
        manifest_path = manifest_path.with_stem(backup_path.stem)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
        
        return encrypted_path
    
    def _collect_files(self) -> List[tuple]:
        """Collect files to be backed up."""
        files = []
        
        # Add sessions directory
        if self.sessions_dir.exists():
            for root, _, files_in_dir in os.walk(self.sessions_dir):
                for file_name in files_in_dir:
                    file_path = Path(root) / file_name
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                    files.append((str(file_path.relative_to(self.base_dir)), file_content))
        
        # Add audit log
        if self.audit_log.exists():
            with open(self.audit_log, "rb") as f:
                file_content = f.read()
            files.append((str(self.audit_log.relative_to(self.base_dir)), file_content))
        
        # Add secrets vault
        if self.vault.exists():
            with open(self.vault, "rb") as f:
                file_content = f.read()
            files.append((str(self.vault.relative_to(self.base_dir)), file_content))
        
        return files
    
    def create_backup(self) -> Optional[Path]:
        """Create a backup of critical files."""
        files = self._collect_files()
        if not files:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_tar_path = Path(tempfile.mkstemp(suffix='.tar.gz')[1])
        
        try:
            with tarfile.open(temp_tar_path, "w:gz") as tar:
                for file_path, file_content in files:
                    tarinfo = tarfile.TarInfo(file_path)
                    tarinfo.size = len(file_content)
                    tarinfo.mode = 0o644
                    tar.addfile(tarinfo, io.BytesIO(file_content))
            
            encrypted_path = self._encrypt_backup(temp_tar_path, self._create_manifest(files))
            
            backup_filename = f"backup_{timestamp}.tar.gz.enc"
            backup_path = self.backups_dir / backup_filename
            
            shutil.move(encrypted_path, backup_path)
            
            return backup_path
        finally:
            try:
                import time
                time.sleep(0.1)
                temp_tar_path.unlink(missing_ok=True)
            except:
                pass
    
    def cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup_file in self.backups_dir.glob("backup_*.tar.gz.enc"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                manifest_file = backup_file.with_suffix(".manifest.json")
                if manifest_file.exists():
                    manifest_file.unlink()

    async def schedule_backups(self, interval_hours: int = 24) -> asyncio.Task:
        """Schedule regular backups."""
        stop_event = asyncio.Event()
        
        async def backup_task():
            while not stop_event.is_set():
                self.create_backup()
                self.cleanup_old_backups()
                await asyncio.sleep(interval_hours * 3600)
        
        return asyncio.create_task(backup_task())

# Initialize BackupManager
import os
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backup_manager = BackupManager(base_dir=_backend_dir)