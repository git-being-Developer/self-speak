# Selfspeak - Start Frontend Server
# This script starts a simple HTTP server for the frontend

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Selfspeak Frontend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "✓ Python found" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting frontend server on http://localhost:3000" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available pages:" -ForegroundColor Cyan
    Write-Host "  - Login:    http://localhost:3000/login.html" -ForegroundColor White
    Write-Host "  - Main App: http://localhost:3000/index.html" -ForegroundColor White
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # Start Python HTTP server
    python -m http.server 3000
} else {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python or use an alternative:" -ForegroundColor Yellow
    Write-Host "  1. Install Python from python.org" -ForegroundColor White
    Write-Host "  2. Use VS Code Live Server extension" -ForegroundColor White
    Write-Host "  3. Use: npx http-server -p 3000" -ForegroundColor White
    Write-Host ""
}
