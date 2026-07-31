# PowerShell script to start MOZA backend
# Exit immediately on errors
$ErrorActionPreference = "Stop"

# Set PYTHONPATH
$env:PYTHONPATH = "D:\Moza\backend;$env:PYTHONPATH"

# Change to backend directory
Set-Location "D:\Moza\backend"

Write-Host "=== STARTING MOZA BACKEND ==="
Write-Host "Directory: $(Get-Location)"
Write-Host "PythonPath: $env:PYTHONPATH"
Write-Host "Starting backend on port 8001..."

# Start backend using python module
python moza/main.py
