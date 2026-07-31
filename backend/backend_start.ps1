Import-Module -DisableNameChecking -Name Console

$ErrorActionPreference = "Stop"

# Clear screen
Clear-Host

Write-Host "=== MOZA BACKEND LAUNCHER ===" -ForegroundColor Yellow
Write-Host "Working Directory: $pwd" -ForegroundColor White

# Set environment variables
$env:PYTHONPATH = "D:\\Moza\\backend;$env:PYTHONPATH"

Write-Host "Setting PYTHONPATH: $env:PYTHONPATH" -ForegroundColor White

# Create log files
"D:\\Moza\\backend\\server_out.log".EnsureDirectory().Clear()
"D:\\Moza\\backend\\server_err.log".EnsureDirectory().Clear()

Write-Host "✓ Environment configured" -ForegroundColor Green

# Test imports
Write-Host "Testing Python imports..." -ForegroundColor Yellow

$importTests = @(
    @("from moza.config.models import MOZAConfig", "MOZAConfig"),
    @("from moza.core.response_normalizer import normalize_streaming_chunk, normalize_response_content", "response_normalizer"),
    @("from moza.gateway.litellm_adapter import LiteLLMAdapter", "litellm_adapter"),
    @("from moza.main import app", "moza.main")
)

foreach ($test in $importTests) {
    $importStmt = $test[0]
    $moduleName = $test[1]
    
    try {
        python -c $importStmt
        Write-Host "✓ $moduleName imported successfully" -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed to import $moduleName : $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ All critical imports successful" -ForegroundColor Green

# Start backend
Write-Host "\nStarting MOZA backend..." -ForegroundColor Yellow
Write-Host "Backend will be available at: http://localhost:8001" -ForegroundColor White

# Start the backend process
try {
    $process = Start-Process -Wait -NoNewWindow -FilePath "python" -ArgumentList "-c \"import sys; sys.path.insert(0, 'D:\\Moza\\backend'); from moza.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8001, log_level='info')\"" -RedirectStandardOutput "D:\\Moza\\backend\\server_out.log" -RedirectStandardError "D:\\Moza\\backend\\server_err.log"
    
    if ($process.ExitCode -eq 0) {
        Write-Host "✓ Backend started successfully" -ForegroundColor Green
        Write-Host "✓ Logs: D:\\Moza\\backend\\server_out.log" -ForegroundColor White
        Write-Host "✓ Errors: D:\\Moza\\backend\\server_err.log" -ForegroundColor White
        Write-Host "\n=== BACKEND OPERATIONAL ===" -ForegroundColor Green
        Write-Host "✅ Backend is now running and ready to accept connections!" -ForegroundColor Green
        Write-Host "✅ UI can connect to: http://localhost:8001" -ForegroundColor Green
    } else {
        Write-Host "✗ Backend failed to start (Exit code: $($process.ExitCode))" -ForegroundColor Red
        Write-Host "Check D:\\Moza\\backend\\server_err.log for errors" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "✗ Error launching backend: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
