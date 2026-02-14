from fastapi import FastAPI
from mangum import Mangum
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the FastAPI app from backend
from backend.main import app

# Wrap FastAPI with Mangum for AWS Lambda/Vercel compatibility
handler = Mangum(app)
