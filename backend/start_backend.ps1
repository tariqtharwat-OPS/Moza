# Simple backend starter script for Windows PowerShell

$ErrorActionPreference = "Stop"

# Change to backend directory
Set-Location "D:\Moza\backend"

# Set PYTHONPATH
$env:PYTHONPATH = "D:\\Moza\\backend;$env:PYTHONPATH"

Write-Host "=== STARTING MOZA BACKEND ===" -ForegroundColor Yellow
Write-Host "Working Directory: $(Get-Location)" -ForegroundColor White
Write-Host "PythonPATH: $env:PYTHONPATH" -ForegroundColor White

# Test critical imports
Write-Host "Testing critical imports..." -ForegroundColor Green

$testImport = @()

# Test response_normalizer
try {
    $testImport += "from moza.core.response_normalizer import normalize_streaming_chunk"
    Write-Host "Response normalizer import successful" -ForegroundColor Green
} catch {
    Write-Host "Response normalizer import failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test litellm_adapter
try {
    $testImport += "from moza.gateway.litellm_adapter import LiteLLMAdapter"
    Write-Host "LiteLLMAdapter import successful" -ForegroundColor Green
} catch {
    Write-Host "LiteLLMAdapter import failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test moza.main
try {
    $testImport += "from moza.main import app"
    Write-Host "Moza main import successful" -ForegroundColor Green
} catch {
    Write-Host "Moza main import failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Import uvicorn
try {
    $testImport += "import uvicorn"
    Write-Host "Uvicorn import successful" -ForegroundColor Green
} catch {
    Write-Host "Uvicorn import failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "\n✓ All critical imports successful!" -ForegroundColor Green

# Start the backend
Write-Host "\nStarting FastAPI backend..." -ForegroundColor Yellow
Write-Host "Backend will be available at: http://0.0.0.0:8001" -ForegroundColor White
Write-Host "UI access: http://localhost:8001" -ForegroundColor White
Write-Host "\nPress Ctrl+C to stop the server" -ForegroundColor Yellow

# Start the backend using uvicorn
try {
    uvicorn.run("moza.main:app", host="0.0.0.0", port=8001, log_level="info")
} catch {
    Write-Host "✗ Error starting backend: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
