#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set PYTHONPATH
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__)) + ';' + os.environ.get('PYTHONPATH', '')

print("=== STARTING MOZA BACKEND ===")
print(f"Working Directory: {os.getcwd()}")
print(f"PythonPath: {os.environ.get('PYTHONPATH')}")

# Import and run the backend directly
try:
    print("Starting FastAPI backend on port 8001...")
    from moza.main import app
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001, reload=False)
except Exception as e:
    print(f"ERROR: Failed to start backend: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
