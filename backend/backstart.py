import sys
import os

# Change to the backend directory
os.chdir("D:/Moza/backend")

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

print("=== MOZA BACKEND LAUNCHER ===")
print(f"Working Directory: {os.getcwd()}")
print(f"Python Path: {sys.path[:3]}")

# Test critical imports
try:
    print("\n1. Importing moza.main module...")
    from moza.main import app
    print("   ✓ moza.main imported successfully")
    
    print("2. Importing uvicorn...")
    import uvicorn
    print("   ✓ uvicorn imported successfully")
    
    print("3. Starting FastAPI server...")
    print("   Host: 0.0.0.0")
    print("   Port: 8001")
    
    # Start the server
    print("\n" + "="*60)
    print("MOZA Backend is now running!")
    print("Server URL: http://0.0.0.0:8001")
    print("UI access: http://localhost:8001")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    
except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print("Please check if all dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
