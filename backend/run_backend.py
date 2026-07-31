#!/usr/bin/env python3
import sys
import os

# Set the working directory to the backend root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

print("=== STARTING MOZA BACKEND ===")
print(f"Working Directory: {os.getcwd()}")
print(f"PythonPath: {':'.join(sys.path[:3])}")

# Test critical imports
print("\n=== Testing Critical Imports ===")
try:
    print("1. Testing moza.config.models...")
    from moza.config.models import MOZAConfig
    print("   ✓ MOZAConfig imported successfully")
    
    print("2. Testing moza.core.response_normalizer...")
    from moza.core.response_normalizer import normalize_streaming_chunk, normalize_response_content
    print("   ✓ response_normalizer imported successfully")
    
    print("3. Testing moza.gateway.litellm_adapter...")
    from moza.gateway.litellm_adapter import LiteLLMAdapter
    print("   ✓ litellm_adapter imported successfully")
    
    print("4. Testing moza.main module...")
    from moza.main import app
    print("   ✓ moza.main imported successfully")
    
    print("\n=== All Imports Successful ===")
    print("Starting FastAPI backend on port 8001...")
    
except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print(f"Error type: {type(e).__name__}")
    print(f"Failed to import module. Please check project structure.")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Import uvicorn and run the backend
try:
    import uvicorn
    print("\n=== Starting Uvicorn Server ===")
    
    config = uvicorn.Config(
        app=app,
        host='0.0.0.0',
        port=8001,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    server.run()
    
except Exception as e:
    print(f"\n✗ Error starting Uvicorn server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
