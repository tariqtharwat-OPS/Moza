#!/usr/bin/env python3
import sys
import os

# Set working directory to backend root
os.chdir('D:/Moza/backend')

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

print("=== MOZA BACKEND STARTUP ===")
print(f"Working Directory: {os.getcwd()}")
print(f"PythonPath: {sys.path[0]}")

# Test all critical imports
print("\n=== Testing Critical Imports ===")

# Import the main module directly
try:
    print("1. Importing moza.main...")
    from moza.main import app
    print("   ✓ moza.main imported successfully")
    
    print("2. Importing uvicorn...")
    import uvicorn
    print("   ✓ uvicorn imported successfully")
    
    print("\n=== All Dependencies Available ===")
    print("Starting FastAPI server on port 8001...")
    
    # Run the server
    uvicorn.run(app, host='0.0.0.0', port=8001, log_level="info")
    
except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print("Failed to import required modules. Please check if all dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error starting backend: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
