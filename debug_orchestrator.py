#!/usr/bin/env python3
"""Debug script to check orchestrator import."""

import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    from moza_orchestrator import MozaOrchestrator
    print("SUCCESS: MozaOrchestrator imported successfully")
    
    # Test basic functionality
    orchestrator = MozaOrchestrator()
    print("SUCCESS: MozaOrchestrator instance created")
    
    # Test getting stats
    stats = orchestrator.get_stats()
    print(f"SUCCESS: Stats retrieved: {stats}")
    
except ImportError as e:
    print(f"FAILED: Import failed: {e}")
    
    # Try importing with different paths
    orchestrator_path = Path(__file__).parent / "packages" / "moza-orchestrator" / "src"
    print(f"Trying path: {orchestrator_path}")
    
    if orchestrator_path.exists():
        sys.path.insert(0, str(orchestrator_path))
        try:
            from moza_orchestrator import MozaOrchestrator
            print("SUCCESS: MozaOrchestrator imported with manual path")
        except ImportError as e2:
            print(f"FAILED: Still failed: {e2}")
    else:
        print(f"FAILED: Path does not exist: {orchestrator_path}")