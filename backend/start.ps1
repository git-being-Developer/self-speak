# Selfspeak Backend Startup Script
# Run this script to start the development server

Write-Host "🌟 Starting Selfspeak Backend..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "⚠️  Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
    Write-Host ""
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Check if requirements are installed
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
$installed = pip freeze
if ($installed -notmatch "fastapi") {
    Write-Host "⚠️  Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}
Write-Host ""

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Red
    Write-Host "   Please copy .env.example to .env and configure your Supabase credentials" -ForegroundColor Yellow
    Write-Host "   Then run this script again" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "✅ Environment variables found" -ForegroundColor Green
Write-Host ""

# Start the server
Write-Host "🚀 Starting FastAPI server..." -ForegroundColor Green
Write-Host "   📍 API: http://localhost:8000" -ForegroundColor White
Write-Host "   📚 Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

python main.py
