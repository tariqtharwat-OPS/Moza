import subprocess
import os
import sys

# Set the working directory to the backend directory
backend_dir = os.path.abspath("D:/Moza/backend")
os.chdir(backend_dir)

# Set PYTHONPATH to include the project directory
os.environ['PYTHONPATH'] = f"{backend_dir}:{os.environ.get('PYTHONPATH', '')}"

print(f"Starting MOZA backend from directory: {backend_dir}")
print(f"PYTHONPATH: {os.environ['PYTHONPATH']}")

# Start the backend using subprocess
# We need to pass the correct Python arguments
subprocess.run([
    sys.executable, "-c", 
    """
import sys
import os
sys.path.insert(0, r'D:/Moza/backend')
from moza.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8001, log_level='info')
"""
], cwd=backend_dir)
