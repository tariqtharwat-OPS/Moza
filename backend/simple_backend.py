import sys
import os

# Set working directory
os.chdir("D:/Moza/backend")

# Critical imports first
try:
    from moza.main import app
    import uvicorn
    print("✓ Imports completed successfully")
    print("✓ Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
