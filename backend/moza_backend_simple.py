#!/usr/bin/env python3
"""
Simple MOZA Backend Launcher
"""
import sys
import os

# Set to backend directory
backend_dir = os.path.abspath('D:/Moza/backend')
os.chdir(backend_dir)

# Set PYTHONPATH
sys.path.insert(0, backend_dir)

print("Starting MOZA backend from:", backend_dir)
print("Python path:", sys.path[0])

# Test critical imports
try:
    from moza.main import app
    print("✓ Backend module imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Import uvicorn
try:
    import uvicorn
    print("✓ Uvicorn imported successfully")
except ImportError as e:
    print(f"✗ Uvicorn import failed: {e}")
    sys.exit(1)

print("\nStarting FastAPI server on port 8001...")
print("Server URL: http://0.0.0.0:8001")
print("UI: http://localhost:8001")

# Start the server
uvicorn.run(app, host='0.0.0.0', port=8001, log_level='info')
