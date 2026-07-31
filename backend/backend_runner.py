#!/usr/bin/env python3
"""
MOZA Backend Launcher
This script starts the FastAPI backend server for MOZA.
"""

import os
import sys

# Set the working directory to the backend root
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

# Test critical imports before proceeding
print("✓ Starting MOZA backend launcher...")

# Import the main FastAPI application
from moza.main import app

# Import uvicorn server
import uvicorn

print("✓ Imports completed successfully")
print("✓ Starting FastAPI server on port 8001...")
print("✓ Server accessible at: http://0.0.0.0:8001")

# Run the FastAPI server via uvicorn
# This will block and start the server
uvicorn.run(app, host='0.0.0.0', port=8001, log_level="info")
