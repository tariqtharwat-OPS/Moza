import sys
import os

# Set the working directory to backend
os.chdir("D:/Moza/backend")

# Add the backend directory to Python path
sys.path.insert(0, "D:/Moza/backend")

# Now run the main module
from moza.main import app
import uvicorn

print("Starting MOZA backend on port 8001...")
print("Server will be available at: http://localhost:8001")
print("Press Ctrl+C to stop the server")

uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
