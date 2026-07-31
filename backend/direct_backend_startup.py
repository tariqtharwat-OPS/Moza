import sys
import os

# Set working directory and Python path
os.chdir("D:/Moza/backend")
sys.path.insert(0, os.getcwd())

print("=== DIRECT BACKEND IMPORT TEST ===")
print(f"Working Directory: {os.getcwd()}")
print(f"Python Path: {sys.path[:3]}")

# Test critical imports
try:
    print("\n1. Importing moza.main...")
    from moza.main import app
    print("   ✓ moza.main imported successfully")
    
    print("2. Importing uvicorn...")
    import uvicorn
    print("   ✓ uvicorn imported successfully")
    
    print("3. Starting FastAPI server...")
    
    # Start the server using uvicorn.run() directly
    print("   Server starting on port 8001...")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    
except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print("Please check if all modules are available.")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
