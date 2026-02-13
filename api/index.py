# Vercel serverless function entry point
from backend.main import app

# Vercel expects the app to be available at module level
handler = app
