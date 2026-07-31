#!/usr/bin/env python3
"""
Ultra-fast MOZA Backend Launcher
This is a simple script designed to start the backend without complex shell commands
"""

import sys
import os

# Set to backend directory
backend_dir = os.path.abspath("D:\Moza\backend")
os.chdir(backend_dir)

# Set Python path
sys.path.insert(0, backend_dir)

print("=== MOZA BACKEND LAUNCHER (DIRECT EXECUTION) ===")
print(f"Working directory: {os.getcwd()}")

# Try importing the backend module
try:
    print("1. Importing moza.main...")
    from moza.main import app
    print("   ✓ moza.main imported successfully")
    
    print("2. Importing uvicorn...")
    import uvicorn
    print("   ✓ uvicorn imported successfully")
    
    print("3. Starting FastAPI server...")
    uvicorn.run(app, host='0.0.0.0', port=8001, log_level="info")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Runtime error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
