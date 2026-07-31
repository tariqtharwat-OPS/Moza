param(
    [string]$BackendPath = "D:\\Moza\\backend",
    [int]$BackendPort = 8001
)

# Exit immediately on errors
$ErrorActionPreference = "Stop"

# Set Python path
$env:PYTHONPATH = "$BackendPath;$env:PYTHONPATH"

# Clear previous log files
"$BackendPath\\server_out.log".EnsureDirectory().Clear()
"$BackendPath\\server_err.log".EnsureDirectory().Clear()

Write-Host "=== STARTING MOZA BACKEND ===" -ForegroundColor Cyan
Write-Host "Working Directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host "PythonPath: $env:PYTHONPATH" -ForegroundColor Yellow

# Test critical imports
Write-Host "Testing critical imports..." -ForegroundColor Green
try {
    Add-Content -Path "$BackendPath\\test_import.log" -Value "Testing imports at $(Get-Date)"
    
    # Import response_normalizer
    Import-Module "$BackendPath\\moza\\core\\response_normalizer.py" -ErrorAction Stop
    Write-Host "✓ response_normalizer imported successfully" -ForegroundColor Green
    
    # Import litellm_adapter
    Import-Module "$BackendPath\\moza\\gateway\\litellm_adapter.py" -ErrorAction Stop
    Write-Host "✓ litellm_adapter imported successfully" -ForegroundColor Green
    
    # Import main application
    Import-Module "$BackendPath\\moza\\main.py" -ErrorAction Stop
    Write-Host "✓ moza.main imported successfully" -ForegroundColor Green
    
} catch {
    Write-Host "✗ Import test failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Starting backend on port $BackendPort..." -ForegroundColor Yellow

try {
    # Start FastAPI server
    Start-Process -FilePath "python" -ArgumentList "$BackendPath\\moza\\main.py" -NoNewWindow -RedirectStandardOutput "$BackendPath\\server_out.log" -RedirectStandardError "$BackendPath\\server_err.log"
    
    # Wait for server to start
    Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Check if server is running
    $response = Invoke-WebRequest -Uri "http://localhost:$BackendPort/v1/orchestrator/info" -Method Get -UseBasicParsing -ErrorAction SilentlyContinue
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Backend started successfully on port $BackendPort" -ForegroundColor Green
        Write-Host "Backend health check passed" -ForegroundColor Green
        
        # Keep the script running
        Write-Host "Backend is running. Press Ctrl+C to stop." -ForegroundColor Yellow
        while ($true) { Start-Sleep -Seconds 1 }
    } else {
        Write-Host "✗ Backend returned unexpected status: $($response.StatusCode)" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "✗ Error starting backend: $($_.Exception.Message)" -ForegroundColor Red
    
    # Check error logs
    if (Test-Path "$BackendPath\\server_err.log") {
        Write-Host "Last 20 lines of error log:" -ForegroundColor Red
        Get-Content "$BackendPath\\server_err.log" -Tail 20 | Write-Host -ForegroundColor Red
    }
    
    exit 1
}
