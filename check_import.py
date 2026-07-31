#!/usr/bin/env python3
"""Simple test to check orchestrator import."""

import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

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
    print("Python path:")
    for p in sys.path:
        print(f"  {p}")
    
    # Check if the package is installed
    try:
        import pkg_resources
        dists = [d for d in pkg_resources.working_set if 'moza' in d.project_name.lower()]
        print("Installed moza packages:")
        for d in dists:
            print(f"  {d.project_name}=={d.version}")
    except Exception as e:
        print(f"Failed to check installed packages: {e}")