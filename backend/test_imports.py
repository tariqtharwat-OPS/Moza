import os
import sys

# Try changing to the backend directory directly
os.chdir("D:/Moza/backend")

print("Current working directory:", os.getcwd())
print("Python path:", sys.path[:3])

# Test imports
try:
    print("\n1. Importing moza.config.models...")
    from moza.config.models import MOZAConfig
    print("   ✓ MOZAConfig imported successfully")
    
    print("\n2. Importing moza.core.response_normalizer...")
    from moza.core.response_normalizer import normalize_streaming_chunk, normalize_response_content
    print("   ✓ response_normalizer imported successfully")
    
    print("\n3. Importing moza.gateway.litellm_adapter...")
    from moza.gateway.litellm_adapter import LiteLLMAdapter
    print("   ✓ litellm_adapter imported successfully")
    
    print("\n4. Importing moza.main...")
    from moza.main import app
    print("   ✓ moza.main imported successfully")
    
    print("\n5. Checking moza directory structure...")
    moza_dir = os.listdir(".")
    print(f"   moza directory exists and contains: {moza_dir}")
    
    print("\n✓ All imports successful!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
