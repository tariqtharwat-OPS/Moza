#!/usr/bin/env python3
import sys
import os

# Set working directory to backend
os.chdir("D:/Moza/backend")

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

print("=== TESTING DIRECT BACKEND IMPORT ===")
print(f"Working Directory: {os.getcwd()}")

# Test imports
try:
    print("\n1. Importing moza modules...")
    from moza.main import app
    print("   ✓ moza.main imported successfully")
    
    print("2. Importing uvicorn...")
    import uvicorn
    print("   ✓ uvicorn imported successfully")
    
    print("\n3. Starting FastAPI server...")
    print("   Host: 0.0.0.0")
    print("   Port: 8001")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    
except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print("Please check if the 'moza' package is properly installed or accessible")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
