import sys
import os
import importlib.util

# Set working directory to the backend directory
backend_dir = os.path.abspath('D:/Moza/backend')
os.chdir(backend_dir)

# Add current directory to Python path
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(backend_dir))

def test_import(name, import_stmt):
    try:
        module = importlib.import_module(name)
        print(f"✓ {import_stmt}")
        return True
    except Exception as e:
        print(f"✗ {import_stmt}: {e}")
        return False

print("=== COMPREHENSIVE MOZA BACKEND IMPORT TEST ===")
print(f"Working Directory: {os.getcwd()}")
print(f"Python Path: {sys.path[0]}")

# Test all critical imports
imports_to_test = [
    ("moza.config.models", "MOZAConfig"),
    ("moza.core.response_normalizer", "normalize_streaming_chunk"),
    ("moza.gateway.litellm_adapter", "LiteLLMAdapter"),
    ("moza.main", "FastAPI app"),
]

all_passed = True
for module_name, description in imports_to_test:
    all_passed &= test_import(module_name, description)

if all_passed:
    print("\n✓ All critical imports successful!")
    print("Backend components are ready for startup.")
    
    # Try to import and start the FastAPI app
    try:
        from moza.main import app
        print("✓ FastAPI app imported successfully")
        
        # Check if uvicorn is available
        try:
            import uvicorn
            print("✓ uvicorn is available")
            
            print("\n=== SERVER STARTUP ===")
            print("Starting MOZA backend server...")
            print("Server will run on: http://0.0.0.0:8001")
            print("Press Ctrl+C to stop the server")
            
            # Start the server
            uvicorn.run(app, host='0.0.0.0', port=8001, log_level="info")
            
        except ImportError:
            print("✗ uvicorn is not available")
            all_passed = False
            
    except Exception as e:
        print(f"✗ Error starting FastAPI app: {e}")
        all_passed = False
else:
    print("\n✗ Some imports failed!")
    print("Please check the project structure and dependencies.")

if not all_passed:
    sys.exit(1)
