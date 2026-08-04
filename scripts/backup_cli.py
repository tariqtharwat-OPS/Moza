"""
Backup CLI for Moza.

Usage:
    python backup_cli.py create
    python backup_cli.py list
    python backup_cli.py restore <filename> [--yes]
    python backup_cli.py cleanup
"""

import argparse
import json
import os
import requests
import sys
from pathlib import Path
from typing import Optional


# Constants
BASE_URL = "http://localhost:8001"
ADMIN_TOKEN = "admin_token_here"  # Replace with actual token or fetch from env


def create_backup():
    """Create a backup."""
    url = f"{BASE_URL}/admin/backup"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            print("Backup created successfully!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed to create backup: {response.text}")
    except Exception as e:
        print(f"Error creating backup: {e}")


def list_backups():
    """List available backups."""
    url = f"{BASE_URL}/admin/backups"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("Available backups:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed to list backups: {response.text}")
    except Exception as e:
        print(f"Error listing backups: {e}")


def restore_backup(filename: str, confirm: bool = False):
    """Restore a backup."""
    if not confirm:
        print(f"Warning: This will restore backup {filename}. Add --yes to confirm.")
        return
    
    url = f"{BASE_URL}/admin/restore/{filename}"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            print(f"Backup {filename} restored successfully!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed to restore backup: {response.text}")
    except Exception as e:
        print(f"Error restoring backup: {e}")


def cleanup_backups():
    """Clean up old backups."""
    print("Cleanup functionality will be implemented in the backend.")


def main():
    parser = argparse.ArgumentParser(description="Moza Backup CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a backup")
    create_parser.set_defaults(func=create_backup)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.set_defaults(func=list_backups)
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore a backup")
    restore_parser.add_argument("filename", help="Backup filename to restore")
    restore_parser.add_argument("--yes", action="store_true", help="Confirm restore action")
    restore_parser.set_defaults(func=lambda args: restore_backup(args.filename, args.yes))
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    cleanup_parser.set_defaults(func=cleanup_backups)
    
    args = parser.parse_args()
    args.func()


if __name__ == "__main__":
    main()