#!/usr/bin/env python3
import sys
import os

# Set the working directory to the backend
backend_dir = os.path.abspath("D:/Moza/backend")
os.chdir(backend_dir)

# Add current directory to Python path
sys.path.insert(0, backend_dir)

# Import dependencies
from moza.main import app
import uvicorn

print("=== STARTING MOZA BACKEND SERVER ===")
print(f"Working Directory: {os.getcwd()}")
print(f"Server URL: http://0.0.0.0:8001")

# Start the server
uvicorn.run(app, host='0.0.0.0', port=8001, log_level="info")
