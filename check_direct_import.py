#!/usr/bin/env python3
"""Direct import test from src directory."""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "packages" / "moza-orchestrator" / "src"
sys.path.insert(0, str(src_path))

print(f"Trying to import from: {src_path}")

try:
    from orchestrator import MozaOrchestrator
    print("SUCCESS: Direct import from orchestrator.py successful")
    
    # Test basic functionality
    orchestrator = MozaOrchestrator()
    print("SUCCESS: MozaOrchestrator instance created")
    
    # Test getting stats
    stats = orchestrator.get_stats()
    print(f"SUCCESS: Stats retrieved: {stats}")
    
except ImportError as e:
    print(f"FAILED: Direct import failed: {e}")
    
    # Check what files are in the src directory
    print("Files in src directory:")
    for f in src_path.iterdir():
        print(f"  {f}")
        
    # Check if the orchestrator.py file exists
    orchestrator_file = src_path / "orchestrator.py"
    if orchestrator_file.exists():
        print(f"SUCCESS: orchestrator.py exists at {orchestrator_file}")
    else:
        print(f"FAILED: orchestrator.py not found at {orchestrator_file}")